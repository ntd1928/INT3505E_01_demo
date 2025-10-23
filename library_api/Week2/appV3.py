from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import hashlib
import json
from functools import wraps
import db
import queries


USER_TOKENS = {
    "token_alice_123": 1,
    "token_bob_456": 2
}

def create_app():
    """
    Version 3: Cacheable (Kế thừa V2)
    Cải tiến: Thêm cơ chế cache bằng ETag vào các response GET.
    - Endpoint GET /books/<id> giờ đây sẽ trả về một ETag header.
    - Client có thể sử dụng ETag này để kiểm tra xem dữ liệu đã thay đổi chưa
      mà không cần tải lại toàn bộ nội dung, giúp tiết kiệm băng thông và
      giảm tải cho server.
    """
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    db_path = os.path.join(app.instance_path, 'library.db')
    app.config.from_mapping(
        DATABASE=db_path,
    )
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if 'Authorization' in request.headers:
                try:
                    token = request.headers['Authorization'].split(" ")[1]
                except IndexError:
                    return jsonify({'message': 'Token format is invalid!'}), 401
            if not token:
                return jsonify({'message': 'Token is missing!'}), 401
            if token not in USER_TOKENS:
                return jsonify({'message': 'Token is invalid!'}), 401
            current_user_id = USER_TOKENS[token]
            return f(current_user_id, *args, **kwargs)
        return decorated
    # === API Endpoints  ===
    @app.route('/')
    def hello():
        return 'Hi! This is V3 - Cacheable.'
    # -- User Endpoints --
    @app.route('/users', methods=['GET'])
    def get_users():
        return jsonify(queries.get_all_users()), 200

    @app.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user = queries.get_user_by_id(user_id)
        if user:
            return jsonify(user), 200
        return jsonify({"message": "User not found"}), 404

    @app.route('/users', methods=['POST'])
    def add_user():
        data = request.get_json()
        if not data or not all(k in data for k in ("name", "email")):
            return jsonify({"message": "Missing required fields: name, email"}), 400
        
        new_user = queries.add_user(data)
        if new_user:
            return jsonify(new_user), 201
        return jsonify({"message": "Email already exists"}), 409

    # === CẢI TIẾN V3: Endpoint GET sách giờ có thể cache ===
    @app.route('/books', methods=['GET'])
    def get_books():
        return jsonify(queries.get_all_books()), 200

    @app.route('/books/<int:book_id>', methods=['GET'])
    def get_book(book_id):
        book = queries.get_book_by_id(book_id)
        if not book:
            return jsonify({"message": "Book not found"}), 404
        
        # 1. Tạo ETag từ hash của nội dung cuốn sách.
        # Dùng json.dumps để đảm bảo dictionary được chuyển thành chuỗi một cách nhất quán.
        book_json_str = json.dumps(book, sort_keys=True).encode('utf-8')
        etag = f'"{hashlib.sha1(book_json_str).hexdigest()}"'
        
        # 2. Kiểm tra header `If-None-Match` từ client gửi lên.
        if request.headers.get('If-None-Match') == etag:
            # Nếu ETag giống nhau, nghĩa là dữ liệu không đổi.
            # Trả về 304 Not Modified.
            return Response(status=304)
        
        # 3. Nếu là lần request đầu tiên hoặc dữ liệu đã thay đổi,
        # trả về response đầy đủ kèm theo header ETag.
        response = jsonify(book)
        response.headers['ETag'] = etag
        return response, 200

    @app.route('/books', methods=['POST'])
    def add_book():
        data = request.get_json()
        if not data or not all(k in data for k in ("title", "author", "year")):
            return jsonify({"message": "Missing required fields: title, author, year"}), 400
        
        new_book = queries.add_book(data)
        return jsonify(new_book), 201
    @app.route('/books/<int:book_id>', methods=['PUT'])
    def update_book(book_id):
        if not queries.get_book_by_id(book_id):
            return jsonify({"message": "Book not found"}), 404

        data = request.get_json()
        if not data or not all(k in data for k in ("title", "author", "year")):
            return jsonify({"message": "Missing required fields: title, author, year"}), 400

        updated_book = queries.update_book(book_id, data)
        return jsonify(updated_book), 200

    @app.route('/books/<int:book_id>', methods=['DELETE'])
    def delete_book(book_id):
        book = queries.get_book_by_id(book_id)
        if not book:
            return jsonify({"message": "Book not found"}), 404
        
        if book['status'] == 'borrowed':
            return jsonify({"message": "Cannot delete a borrowed book"}), 409

        if queries.delete_book(book_id):
            return jsonify({"message": f"Book with id {book_id} has been deleted."}), 200
        return jsonify({"message": "An error occurred"}), 500

    # -- Borrow/Return Endpoints --
    @app.route('/books/<int:book_id>/borrow', methods=['POST'])
    def borrow_book_route():
        book = queries.get_book_by_id(book_id)
        if not book: return jsonify({"message": "Book not found"}), 404
        if book['status'] != 'available': return jsonify({"message": "Book is not available"}), 409

        data = request.get_json()
        if not data or 'user_id' not in data: return jsonify({"message": "Missing user_id"}), 400
        
        user = queries.get_user_by_id(data['user_id'])
        if not user: return jsonify({"message": "User not found"}), 404
        
        borrow_record = queries.borrow_book(book_id, data['user_id'])
        if borrow_record:
            return jsonify(borrow_record), 201
        return jsonify({"message": "Failed to borrow book"}), 500

    @app.route('/books/<int:book_id>/return', methods=['POST'])
    def return_book_route():
        book = queries.get_book_by_id(book_id)
        if not book: return jsonify({"message": "Book not found"}), 404
        if book['status'] != 'borrowed': return jsonify({"message": "Book was not borrowed"}), 400
            
        if queries.return_book(book_id):
            return jsonify({"message": f"Book '{book['title']}' has been returned."}), 200
        return jsonify({"message": "Could not find an active borrow record"}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

