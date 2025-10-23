# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS 
import db
import queries

#Sever chỉ xử lí request và trả về response json
def create_app():

    app = Flask(__name__)
    CORS(app)
    db.init_app(app)

    # === API Endpoints ===
    @app.route('/')
    def hello():
        return 'Hi!'
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

    # -- Book Endpoints --
    @app.route('/books', methods=['GET'])
    def get_books():
        return jsonify(queries.get_all_books()), 200

    @app.route('/books/<int:book_id>', methods=['GET'])
    def get_book(book_id):
        book = queries.get_book_by_id(book_id)
        if book:
            return jsonify(book), 200
        return jsonify({"message": "Book not found"}), 404

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