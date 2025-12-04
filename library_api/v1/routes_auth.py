# File: library_api/v1/routes_auth.py

import jwt
import uuid  # Thêm import uuid để tạo jti
from datetime import datetime, timedelta
from flask import request, jsonify, current_app, g
from werkzeug.security import check_password_hash
from . import bp, token_required, limiter   # Sửa lại import để có cả token_required
from .. import queries


@bp.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Giới hạn đăng nhập: 5 lần mỗi phút
def login():
    """
    Xác thực người dùng và trả về một JWT có chứa JTI (JWT ID).
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email và password là bắt buộc."}), 401
    
    email = data['email']
    
    # Ghi log ở cấp độ INFO
    current_app.logger.info(f"Login attempt for user: {email}")

    user = queries.get_user_by_email(email)

    if not user or not check_password_hash(user['password'], data['password']):
        current_app.logger.warning(f"Failed login attempt for user: {email} (Invalid credentials)")
        return jsonify({"message": "Email hoặc password không chính xác."}), 401

    # Tạo JWT payload, bao gồm cả 'jti' để định danh token
    payload = {
        'sub': str(user['id']),
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=60),
        'jti': str(uuid.uuid4())  # Tạo một ID duy nhất cho token này
    }

    # Tạo token
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm="HS256"
    )

    return jsonify({'token': token})

@bp.route('/auth/logout', methods=['POST'])
@token_required  # Yêu cầu phải có token hợp lệ để có thể đăng xuất
def logout():
    """
    Đăng xuất người dùng.
    Hành động này sẽ lấy JTI từ token hiện tại và thêm nó vào blacklist.
    Token này sẽ không thể sử dụng lại được nữa.
    """
    try:
        # Decorator @token_required đã giải mã và lưu payload vào `g.current_token_payload`
        jti = g.current_token_payload['jti']
        
        # Gọi hàm query để thêm jti vào danh sách đen
        queries.add_jti_to_blacklist(jti)
        
        return jsonify({"message": "Đăng xuất thành công."}), 200
    except KeyError:
        # Lỗi này xảy ra nếu payload không có jti (ví dụ: token cũ từ trước khi triển khai)
        return jsonify({"message": "Token không hợp lệ để đăng xuất."}), 400
    except Exception as e:
        # Bắt các lỗi không mong muốn khác
        return jsonify({"message": "Đã xảy ra lỗi trong quá trình đăng xuất."}), 500