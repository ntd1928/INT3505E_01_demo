from flask import Flask, request, jsonify, Response, url_for
import os
import hashlib
import json
from functools import wraps
from flask_cors import CORS 

import db
import queries

USER_TOKENS = {
    "token_alice_123": 1,
    "token_bob_456": 2
}

def create_app():
    """
    Version 4: Uniform Interface (HATEOAS) - Kế thừa V3
    Cải tiến: Thêm các liên kết HATEOAS vào response để API có khả năng "tự mô tả".
    - Client không cần phải hardcode các URL cho hành động (mượn, trả).
    - Server sẽ cung cấp các URL hợp lệ dựa vào trạng thái hiện tại của tài nguyên.
    - Điều này giúp giảm sự phụ thuộc giữa client và server, làm cho API linh hoạt hơn.
    """
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)

    db_path = os.path.join(app.instance_path, 'library.db')
    app.config.from_mapping(DATABASE=db_path)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    # Decorator token_required kế thừa từ V2
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if 'Authorization' in request.headers:
                try: token = request.headers['Authorization'].split(" ")[1]
                except IndexError: return jsonify({'message': 'Token format is invalid!'}), 401
            if not token: return jsonify({'message': 'Token is missing!'}), 401
            if token not in USER_TOKENS: return jsonify({'message': 'Token is invalid!'}), 401
            current_user_id = USER_TOKENS[token]
            return f(current_user_id, *args, **kwargs)
        return decorated

    # === CẢI TIẾN V4: Helper function để thêm các liên kết HATEOAS ===
    def add_hateoas_links_to_book(book):
        """Thêm một trường `_links` vào dictionary của sách."""
        book['_links'] = {
            "self": { "href": url_for('get_book', book_id=book['id'], _external=True) },
            "collection": { "href": url_for('get_books', _external=True) }
        }
        # Chỉ thêm link hành động nếu phù hợp với trạng thái hiện tại
        if book['status'] == 'available':
            book['_links']['borrow'] = { 
                "href": url_for('borrow_book_route', book_id=book['id'], _external=True),
                "method": "POST"
            }
        elif book['status'] == 'borrowed':
            book['_links']['return'] = {
                "href": url_for('return_book_route', book_id=book['id'], _external=True),
                "method": "POST"
            }
        return book
    # === API Endpoints (Kế thừa và cải tiến) ===
    @app.route('/')
    def hello():
        return 'Hi! This is V4 - Uniform Interface (HATEOAS).'
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
    # === CẢI TIẾN V4: Các endpoint GET giờ đây chứa cả _links ===
    @app.route('/books', methods=['GET'])
    def get_books():
        all_books = queries.get_all_books()
        # Thêm _links cho từng cuốn sách trong danh sách
        books_with_links = [add_hateoas_links_to_book(b.copy()) for b in all_books]
        return jsonify(books_with_links), 200

    @app.route('/books/<int:book_id>', methods=['GET'])
    def get_book(book_id):
        book = queries.get_book_by_id(book_id)
        if not book: return jsonify({"message": "Book not found"}), 404
        
        # Thêm các liên kết HATEOAS vào response
        book_with_links = add_hateoas_links_to_book(book.copy())
        
        # Cơ chế ETag từ V3 vẫn hoạt động, nhưng bây giờ dựa trên data đã có links
        book_json_str = json.dumps(book_with_links, sort_keys=True).encode('utf-8')
        etag = f'"{hashlib.sha1(book_json_str).hexdigest()}"'
        
        if request.headers.get('If-None-Match') == etag:
            return Response(status=304)
        
        response = jsonify(book_with_links)
        response.headers['ETag'] = etag
        return response
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
    # borrow, return 
    @app.route('/books/<int:book_id>/borrow', methods=['POST'])
    @token_required
    def borrow_book_route(current_user_id, book_id):
        book = queries.get_book_by_id(book_id)
        if not book: return jsonify({"message": "Book not found"}), 404
        if book['status'] != 'available':
            # Cải tiến nhỏ: Trả về trạng thái hiện tại của sách với HATEOAS
            book_with_links = add_hateoas_links_to_book(book.copy())
            return jsonify({
                "message": "Book is not available",
                "current_state": book_with_links
            }), 409

        borrow_record = queries.borrow_book(book_id, current_user_id)
        if borrow_record:
            # Sau khi mượn thành công, trả về trạng thái mới của sách
            updated_book = queries.get_book_by_id(book_id)
            return jsonify(add_hateoas_links_to_book(updated_book)), 200
        return jsonify({"message": "Failed to borrow book"}), 500

    @app.route('/books/<int:book_id>/return', methods=['POST'])
    @token_required
    def return_book_route(current_user_id, book_id):
        if queries.return_book(book_id):
            updated_book = queries.get_book_by_id(book_id)
            return jsonify(add_hateoas_links_to_book(updated_book)), 200
        return jsonify({"message": "Could not find an active borrow record"}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

