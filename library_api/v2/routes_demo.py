# File: library_api/v2/routes_demo.py

from flask import jsonify
from . import bp

@bp.route('/status', methods=['GET'])
def get_status_v2():
    """
    Endpoint phiên bản 2 (mới).
    Trả về status dưới dạng một đối tượng có cấu trúc.
    """
    # Dữ liệu theo cấu trúc mới (Breaking Change)
    data = {
        "version": "v2",
        "status": {
            "code": 200,
            "message": "OK" # Trả về đối tượng
        }
    }
    return jsonify(data)