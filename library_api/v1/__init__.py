# library_api/v1/__init__.py

from flask import Blueprint, request, jsonify
from functools import wraps

# Tạo một Blueprint tên là 'v1'
bp = Blueprint('v1', __name__)

# Các token giả lập để xác thực
USER_TOKENS = {
    "token_alice_123": 1,
    "token_bob_456": 2
}

# Decorator để yêu cầu token xác thực
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                # Định dạng chuẩn là "Bearer <token>"
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token format is invalid!'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        if token not in USER_TOKENS:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        # Gắn user_id vào request context để các hàm route có thể sử dụng
        # mà không cần truyền qua tham số.
        request.current_user_id = USER_TOKENS[token]
        return f(*args, **kwargs)
    return decorated

# Import các file route ở cuối để tránh lỗi circular import
# Các file này sẽ sử dụng đối tượng `bp` đã được tạo ở trên.
from . import routes_books, routes_borrows, routes_users