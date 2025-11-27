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