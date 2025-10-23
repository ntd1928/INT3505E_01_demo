# library_api/v1/routes_borrows.py

from flask import request, jsonify, url_for, Response
from . import bp, token_required
from .. import queries

# --- Helper Function for HATEOAS ---
def add_hateoas_links_to_borrow(borrow_record):
    """Thêm các liên kết HATEOAS vào đối tượng lượt mượn."""
    borrow_record['_links'] = {
        "self": {"href": url_for('v1.get_borrow_record', borrow_id=borrow_record['borrow_id'], _external=True)},
        "book": {"href": url_for('v1.get_book', book_id=borrow_record['book_id'], _external=True)},
        "user": {"href": url_for('v1.get_user_by_id', user_id=borrow_record['user_id'], _external=True)}
    }
    # Nếu sách chưa được trả, thêm link cho hành động "trả sách"
    if not borrow_record.get('return_date'):
        borrow_record['_links']['return'] = {
            "href": url_for('v1.return_book_by_deleting_borrow', borrow_id=borrow_record['borrow_id'], _external=True),
            "method": "DELETE"
        }
    return borrow_record

# --- API Endpoints ---
@bp.route('/borrows', methods=['POST'])
@token_required
def create_borrow_record():
    """
    Tạo một lượt mượn mới.
    """
    data = request.get_json()
    if not data or 'book_id' not in data:
        return jsonify({"message": "Field 'book_id' is required"}), 400

    book_id = data['book_id']
    user_id = request.current_user_id
    
    book = queries.get_book_by_id(book_id)
    if not book:
        return jsonify({"message": f"Book with id {book_id} not found"}), 404
    if book['status'] != 'available':
        return jsonify({"message": "Book is not available for borrowing"}), 409 # 409 Conflict

    borrow_record = queries.borrow_book(book_id, user_id)
    if borrow_record:
        # Trả về tài nguyên "lượt mượn" vừa tạo, kèm HATEOAS
        return jsonify({"data": add_hateoas_links_to_borrow(borrow_record)}), 201
    return jsonify({"message": "An internal error occurred while borrowing the book"}), 500

@bp.route('/borrows/<int:borrow_id>', methods=['DELETE'])
@token_required
def return_book_by_deleting_borrow(borrow_id):
    """
    Trả sách bằng cách xóa (kết thúc) một lượt mượn. Đúng chuẩn REST.
    """
    # Lấy thông tin lượt mượn để kiểm tra
    borrow_record = queries.get_borrow_by_id(borrow_id)
    if not borrow_record:
        return jsonify({"message": f"Borrow record with id {borrow_id} not found"}), 404

    # (Tùy chọn) Kiểm tra xem người trả có phải là người mượn không
    if borrow_record['user_id'] != request.current_user_id:
        return jsonify({"message": "You are not authorized to return this book"}), 403

    if queries.return_book(borrow_record['book_id']):
        return Response(status=204) # 204 No Content
    return jsonify({"message": "Failed to return book or book was already returned"}), 400

@bp.route('/borrows/<int:borrow_id>', methods=['GET'])
def get_borrow_record(borrow_id):
    record = queries.get_borrow_by_id(borrow_id)
    if not record:
        return jsonify({"message": f"Borrow record with id {borrow_id} not found"}), 404
    return jsonify({"data": add_hateoas_links_to_borrow(record)}), 200

# Endpoint để user xem lịch sử mượn của chính mình
@bp.route('/user/borrows', methods=['GET'])
@token_required
def get_my_borrow_history():
    user_id = request.current_user_id
    history = queries.get_borrows_by_user_id(user_id)
    history_with_links = [add_hateoas_links_to_borrow(b) for b in history]
    return jsonify({"data": history_with_links}), 200

# Thêm route cho User để HATEOAS link hoạt động
@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user = queries.get_user_by_id(user_id)
    if user:
        return jsonify({'data': user}), 200
    return jsonify({"message": "User not found"}), 404