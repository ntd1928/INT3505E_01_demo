# library_api/v1/__init__.py

from flask import Blueprint, request, jsonify, g, current_app
from functools import wraps
import jwt

from .. import queries
# Tạo một Blueprint tên là 'v1'
bp = Blueprint('v1', __name__)



import logging # <<< THÊM IMPORT NÀY

# THAY THẾ TOÀN BỘ DECORATOR CŨ BẰNG PHIÊN BẢN NÀY
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        logging.basicConfig(level=logging.DEBUG) # Bật chế độ debug cho logging
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            logging.warning("TOKEN DEBUG: Token is missing from header.")
            return jsonify({'message': 'Token is missing!'}), 401
        
        # In ra thông tin để debug
        logging.debug(f"TOKEN DEBUG: Received token: {token}")
        logging.debug(f"TOKEN DEBUG: Key used for decoding: {current_app.config['SECRET_KEY']}")

        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            
            jti = payload.get('jti')
            if not jti or queries.is_jti_in_blacklist(jti):
                logging.warning(f"TOKEN DEBUG: JTI {jti} is in blacklist or missing.")
                return jsonify({'message': 'Token has been revoked!'}), 401

            g.current_user_id = int(payload['sub'])
            g.current_token_payload = payload

        except jwt.ExpiredSignatureError:
            logging.error("TOKEN DEBUG: ExpiredSignatureError - Token has expired!")
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError as e:
            # In ra lỗi cụ thể từ thư viện PyJWT
            logging.error(f"TOKEN DEBUG: InvalidTokenError - {str(e)}")
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            # Bắt các lỗi không mong muốn khác
            logging.error(f"TOKEN DEBUG: An unexpected error occurred: {str(e)}")
            return jsonify({'message': 'An internal error occurred.'}), 500

        return f(*args, **kwargs)
    return decorated


# Import các file route ở cuối để tránh lỗi circular import
# Các file này sẽ sử dụng đối tượng `bp` đã được tạo ở trên.
from . import routes_books, routes_borrows, routes_users, routes_auth