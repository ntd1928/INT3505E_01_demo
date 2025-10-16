from flask import Flask, request, jsonify
import os
from functools import wraps
import db
import queries

# === CẢI TIẾN V2: Thêm cơ chế Token ===
# Giả lập token của user.
USER_TOKENS = {
    "token_alice_123": 1,  # token -> user_id
    "token_bob_456": 2
}

def create_app():
    """
    Version 2: Stateless (Kế thừa V1)
    Cải tiến: Thêm xác thực token để thể hiện tính phi trạng thái.
    - Server không lưu trữ session hay bất kỳ trạng thái nào của client.
    - Mỗi request yêu cầu hành động (POST, PUT, DELETE) phải tự chứa thông tin
      xác thực (token) trong header `Authorization`.
    - Điều này giúp hệ thống dễ dàng mở rộng (scale) vì bất kỳ server nào
      trong một cụm cũng có thể xử lý request một cách độc lập.
    """
    app = Flask(__name__, instance_relative_config=True)

    db_path = os.path.join(app.instance_path, 'library.db')
    app.config.from_mapping(
        DATABASE=db_path,
    )

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    # === CẢI TIẾN V2: Decorator để kiểm tra token ===
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            # Client phải gửi token theo format: "Bearer <token>"
            if 'Authorization' in request.headers:
                try:
                    token = request.headers['Authorization'].split(" ")[1]
                except IndexError:
                    return jsonify({'message': 'Token format is invalid!'}), 401

            if not token:
                return jsonify({'message': 'Token is missing!'}), 401
            
            if token not in USER_TOKENS:
                return jsonify({'message': 'Token is invalid!'}), 401

            # Lấy user_id từ token và truyền vào hàm xử lý route
            current_user_id = USER_TOKENS[token]
            return f(current_user_id, *args, **kwargs)
        return decorated


    # === API Endpoints  ===
    @app.route('/')
    def hello():
        return 'Hi! This is V2 - Stateless.'

    # -- User Endpoints --
    @app.route('/users', methods=['GET'])
    def get_users():
        return jsonify(queries.get_all_users()), 200

    @app.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user = queries.get_user_by_id(user_id)
        if user: return jsonify(user), 200
        return jsonify({"message": "User not found"}), 404

    @app.route('/users', methods=['POST'])
    def add_user():
        data = request.get_json()
        if not data or not all(k in data for k in ("name", "email")):
            return jsonify({"message": "Missing required fields: name, email"}), 400
        new_user = queries.add_user(data)
        if new_user: return jsonify(new_user), 201
        return jsonify({"message": "Email already exists"}), 409

    # -- Book Endpoints  --
    @app.route('/books', methods=['GET'])
    def get_books():
        return jsonify(queries.get_all_books()), 200

    @app.route('/books/<int:book_id>', methods=['GET'])
    def get_book(book_id):
        book = queries.get_book_by_id(book_id)
        if book: return jsonify(book), 200
        return jsonify({"message": "Book not found"}), 404

    # -- Borrow/Return Endpoints (Cải tiến với @token_required) --
    @app.route('/books/<int:book_id>/borrow', methods=['POST'])
    @token_required
    def borrow_book_route(current_user_id, book_id):
        """
        Cải tiến quan trọng của V2:
        - Route này giờ đây yêu cầu xác thực qua token.
        - Không cần gửi `user_id` trong body nữa. Server xác định user
          dựa trên token được gửi trong header.
        - Mỗi request đều độc lập và chứa đủ thông tin để được xử lý.
        """
        book = queries.get_book_by_id(book_id)
        if not book: return jsonify({"message": "Book not found"}), 404
        if book['status'] != 'available': return jsonify({"message": "Book is not available"}), 409

        borrow_record = queries.borrow_book(book_id, current_user_id)
        if borrow_record:
            return jsonify(borrow_record), 201
        return jsonify({"message": "Failed to borrow book"}), 500

    @app.route('/books/<int:book_id>/return', methods=['POST'])
    @token_required
    def return_book_route(current_user_id, book_id):
        # Mặc dù logic trả sách không cần user_id, việc bảo vệ endpoint này
        # đảm bảo chỉ người dùng đã đăng nhập mới có thể thực hiện hành động.
        book = queries.get_book_by_id(book_id)
        if not book: return jsonify({"message": "Book not found"}), 404
        if book['status'] != 'borrowed': return jsonify({"message": "Book was not borrowed"}), 400
            
        if queries.return_book(book_id):
            return jsonify({"message": f"Book '{book['title']}' has been returned."}), 200
        return jsonify({"message": "Could not find an active borrow record"}), 500
    
    # Các endpoint thay đổi dữ liệu khác (POST, PUT, DELETE sách) cũng nên được
    # bảo vệ bằng @token_required trong một ứng dụng thực tế.

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

