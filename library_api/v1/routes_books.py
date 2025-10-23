# library_api/v1/routes_books.py

from flask import request, jsonify, url_for, Response
from . import bp # Import blueprint từ __init__.py
from .. import queries # Import module queries từ thư mục cha

# --- Helper Function for HATEOAS ---
def add_hateoas_links_to_book(book):
    """Thêm các liên kết HATEOAS vào đối tượng sách."""
    book['_links'] = {
        "self": {"href": url_for('v1.get_book', book_id=book['id'], _external=True)}
    }
    if book['status'] == 'available':
        # Hành động "mượn" giờ đây trỏ đến việc tạo một tài nguyên "borrow" mới
        book['_links']['borrow'] = { 
            "href": url_for('v1.create_borrow_record', _external=True),
            "method": "POST",
            "schema": {"book_id": "integer", "description": "ID of the book to borrow"}
        }
    return book

# --- API Endpoints ---
@bp.route('/books', methods=['GET'])
def get_books():
    """
    Lấy danh sách sách, hỗ trợ tìm kiếm, lọc và phân trang.
    Query Params:
    - search: Tìm kiếm theo tiêu đề sách.
    - author: Lọc theo tên tác giả.
    - year: Lọc theo năm xuất bản.
    - page: Trang hiện tại (mặc định 1).
    - limit: Số lượng item trên mỗi trang (mặc định 10).
    """
    # Lấy các query params
    search_term = request.args.get('search')
    author = request.args.get('author')
    year = request.args.get('year', type=int)
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    # Gọi hàm query đã được nâng cấp
    books_data = queries.search_and_filter_books(search_term, author, year, page, limit)
    
    # Thêm HATEOAS links cho mỗi cuốn sách
    books_with_links = [add_hateoas_links_to_book(b.copy()) for b in books_data['items']]

    # Sử dụng response wrapper nhất quán
    response = {
        "data": books_with_links,
        "pagination": books_data['pagination']
    }
    return jsonify(response), 200

@bp.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = queries.get_book_by_id(book_id)
    if not book:
        return jsonify({"message": f"Book with id {book_id} not found"}), 404
    
    book_with_links = add_hateoas_links_to_book(book.copy())
    return jsonify({"data": book_with_links}), 200

@bp.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data or not all(k in data for k in ("title", "author", "year")):
        return jsonify({"message": "Missing required fields: title, author, year"}), 400
    
    new_book = queries.add_book(data)
    return jsonify({"data": new_book}), 201 # 201 Created

@bp.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    if not queries.get_book_by_id(book_id):
        return jsonify({"message": f"Book with id {book_id} not found"}), 404

    data = request.get_json()
    if not data or not all(k in data for k in ("title", "author", "year")):
        return jsonify({"message": "Missing required fields: title, author, year"}), 400

    updated_book = queries.update_book(book_id, data)
    return jsonify({"data": updated_book}), 200

@bp.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = queries.get_book_by_id(book_id)
    if not book:
        return jsonify({"message": f"Book with id {book_id} not found"}), 404
    
    if book['status'] == 'borrowed':
        return jsonify({"message": "Cannot delete a borrowed book. Please return it first."}), 409 # 409 Conflict

    if queries.delete_book(book_id):
        # 204 No Content là response chuẩn cho DELETE thành công
        return Response(status=204)
    return jsonify({"message": "An error occurred during deletion"}), 500