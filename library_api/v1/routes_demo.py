# File: library_api/v1/routes_demo.py

from flask import jsonify, make_response
from . import bp

@bp.route('/status', methods=['GET'])
def get_status_v1():
    """
    Endpoint phiên bản 1 (cũ).
    Trả về status dưới dạng một chuỗi đơn giản.
    """
    # Dữ liệu theo cấu trúc cũ
    data = {
        "version": "v1",
        "status_message": "OK" # Trả về chuỗi
    }
    
    # Tạo đối tượng response để có thể thêm header
    response = make_response(jsonify(data))
    
    # --- TRIỂN KHAI HEADER CẢNH BÁO ---
    response.headers['Warning'] = '299 - "This API version is deprecated and will be removed after 2026-12-31."'
    response.headers['Sunset'] = 'Sat, 31 Dec 2026 23:59:59 GMT'
    response.headers['Link'] = '<http://127.0.0.1:5001/api/v2/status>; rel="successor-version"'
    
    return response
# --- Chiến lược 1: URL Versioning (Cách bạn đã làm) ---
# Endpoint này được kích hoạt thông qua prefix /api/v1 của Blueprint
@bp.route('/info-url', methods=['GET'])
def versioning_by_url():
    """Demo versioning bằng URL. Truy cập qua /api/v1/info-url."""
    return jsonify({
        "strategy": "URL Versioning",
        "version": "v1",
        "message": "Bạn đã gọi phiên bản 1 qua URL."
    })

# --- Chiến lược 2: Header Versioning ---
# Chúng ta cần một route mới không nằm trong prefix /v1.
# Chúng ta sẽ định nghĩa nó trong create_app.
def versioning_by_header():
    """
    Demo versioning bằng Header. 
    Route này sẽ được đăng ký tại /api/info.
    """
    # Lấy phiên bản từ header 'X-API-Version', mặc định là 'unknown'
    version = request.headers.get('X-API-Version', 'unknown')
    
    if version == '1':
        # Logic cho phiên bản 1
        return jsonify({
            "strategy": "Header Versioning",
            "version": "v1",
            "message": "Bạn đã gọi phiên bản 1 qua Header."
        })
    elif version == '2':
        # Logic cho phiên bản 2 (giả lập)
        return jsonify({
            "strategy": "Header Versioning",
            "version": "v2",
            "message": "Đây là logic cho phiên bản 2, được gọi qua Header."
        })
    else:
        return jsonify({"error": "Phiên bản không hợp lệ hoặc không được cung cấp."}), 400

# --- Chiến lược 3: Query Parameter Versioning ---
# Route này cũng sẽ được đăng ký tại một URL chung.
def versioning_by_query_param():
    """
    Demo versioning bằng Query Parameter.
    Route này sẽ được đăng ký tại /api/info-query.
    """
    # Lấy phiên bản từ query param 'version', mặc định là 'unknown'
    version = request.args.get('version', 'unknown')

    if version == '1':
        return jsonify({
            "strategy": "Query Parameter Versioning",
            "version": "v1",
            "message": "Bạn đã gọi phiên bản 1 qua Query Parameter."
        })
    elif version == '2':
        return jsonify({
            "strategy": "Query Parameter Versioning",
            "version": "v2",
            "message": "Đây là logic cho phiên bản 2, được gọi qua Query Parameter."
        })
    else:
        return jsonify({"error": "Phiên bản không hợp lệ hoặc không được cung cấp."}), 400