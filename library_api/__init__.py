import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from prometheus_flask_exporter import PrometheusMetrics

import logging
from logging.config import dictConfig

load_dotenv()

# --- ĐỊNH NGHĨA CẤU HÌNH LOGGING ---
# Cấu hình này sẽ ghi log ra file `instance/app.log`
# và vẫn hiển thị trên console.
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'instance/app.log', # Ghi log vào thư mục instance
            'maxBytes': 1024 * 1024, # 1 MB
            'backupCount': 5,
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO', # Cấp độ log mặc định
        'handlers': ['console', 'file']
    }
})

def create_app():
    """
    Hàm khởi tạo ứng dụng Flask (Application Factory).
    """
    app = Flask(__name__, instance_relative_config=True)
    metrics = PrometheusMetrics(app)
    CORS(app)

    # --- ĐĂNG KÝ CÁC ROUTE DEMO CHO HEADER VÀ QUERY PARAM ---
    # Import các hàm demo từ v1 (hoặc một module chung)
    from .v1.routes_demo import versioning_by_header, versioning_by_query_param

    # Đăng ký route cho Header Versioning
    app.add_url_rule('/api/info-header', 'info_header', versioning_by_header, methods=['GET'])

    # Đăng ký route cho Query Parameter Versioning
    app.add_url_rule('/api/info-query', 'info_query', versioning_by_query_param, methods=['GET'])

    # Cấu hình database
    db_path = os.path.join(app.instance_path, 'library.db')
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'default-secret-key-for-dev'),
        DATABASE=db_path,
    )
    
    print(f"--- [DEBUG] SECRET_KEY IN USE: {app.config['SECRET_KEY']} ---")

    # Đảm bảo thư mục instance tồn tại
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Khởi tạo DB
    from . import db
    db.init_app(app)

    # --- ĐĂNG KÝ BLUEPRINT CHO API V1 ---
    from .v1 import bp as v1_blueprint, limiter as v1_limiter     
    app.register_blueprint(v1_blueprint, url_prefix='/api/v1')

    v1_limiter.init_app(app)
    
    # --- ĐĂNG KÝ BLUEPRINT CHO API V2 ---
    from .v2 import bp as v2_blueprint
    app.register_blueprint(v2_blueprint, url_prefix='/api/v2')

    # Handler lỗi chung để trả về JSON nhất quán
    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify(error="The requested resource was not found."), 404

    # Route gốc để kiểm tra server có hoạt động không
    @app.route('/')
    def index():
        return "Library API server is running. Use endpoints under /api/v1/"

    return app