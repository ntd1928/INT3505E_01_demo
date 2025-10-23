# library_api/v1/routes_users.py

from flask import request, jsonify, url_for
from . import bp # Import blueprint từ __init__.py
from .. import queries # Import module queries từ thư mục cha

# --- API Endpoints ---

@bp.route('/users', methods=['GET'])
def get_users():
    """Lấy danh sách tất cả người dùng."""
    all_users = queries.get_all_users()
    # Sử dụng response wrapper nhất quán
    return jsonify({"data": all_users}), 200

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Lấy thông tin chi tiết của một người dùng cụ thể."""
    user = queries.get_user_by_id(user_id)
    if not user:
        return jsonify({"message": f"User with id {user_id} not found"}), 404
    
    return jsonify({"data": user}), 200

@bp.route('/users', methods=['POST'])
def create_user():
    """Tạo một người dùng mới."""
    data = request.get_json()
    if not data or not all(k in data for k in ("name", "email")):
        return jsonify({"message": "Missing required fields: name, email"}), 400
    
    # Hàm add_user trong queries.py sẽ trả về None nếu email bị trùng
    new_user = queries.add_user(data)
    
    if new_user:
        # Trả về thông tin người dùng vừa tạo với status 201 Created
        return jsonify({"data": new_user}), 201
    else:
        # Nếu email đã tồn tại, trả về lỗi 409 Conflict
        return jsonify({"message": f"User with email '{data['email']}' already exists."}), 409

@bp.route('/users/<int:user_id>/borrows', methods=['GET'])
def get_borrows_for_user(user_id):
    """
    Lấy danh sách các sách mà một người dùng đang mượn (Nested Route).
    Đây là một ví dụ về cách thiết kế API cho các tài nguyên liên quan.
    """
    # Đầu tiên, kiểm tra xem user có tồn tại không
    user = queries.get_user_by_id(user_id)
    if not user:
        return jsonify({"message": f"User with id {user_id} not found"}), 404

    # Nếu user tồn tại, lấy danh sách sách họ đang mượn
    borrowed_books = queries.get_borrowed_books_by_user(user_id)
    
    return jsonify({"data": borrowed_books}), 200