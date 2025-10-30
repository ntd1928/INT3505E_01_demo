import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

def create_app():
    """
    Hàm khởi tạo ứng dụng Flask (Application Factory).
    """
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)

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
    from .v1 import bp as v1_blueprint
    app.register_blueprint(v1_blueprint, url_prefix='/api/v1')

    # Handler lỗi chung để trả về JSON nhất quán
    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify(error="The requested resource was not found."), 404

    # Route gốc để kiểm tra server có hoạt động không
    @app.route('/')
    def index():
        return "Library API server is running. Use endpoints under /api/v1/"

    return app