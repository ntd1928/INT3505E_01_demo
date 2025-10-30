from .db import get_db
from datetime import datetime
from werkzeug.security import generate_password_hash

# === USER QUERIES ===
def get_all_users():
    conn = get_db()
    users = conn.execute('SELECT * FROM users').fetchall()
    return [dict(user) for user in users]

def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return dict(user) if user else None

def add_user(data):
    conn = get_db()
    cursor = conn.cursor()
    member_since = datetime.now().strftime("%Y-%m-%d")
    
    # Băm mật khẩu người dùng cung cấp trước khi lưu vào DB
    hashed_password = generate_password_hash(data['password'])
    
    try:
        # Sửa câu lệnh INSERT để thêm cả cột password
        cursor.execute('INSERT INTO users (name, email, password, member_since) VALUES (?, ?, ?, ?)',
                       (data['name'], data['email'], hashed_password, member_since))
        conn.commit()
        new_user_id = cursor.lastrowid
        return get_user_by_id(new_user_id)
    except conn.IntegrityError:
        return None
def get_user_by_email(email):
    """Lấy thông tin người dùng dựa trên địa chỉ email."""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    # Trả về một dictionary nếu tìm thấy user, ngược lại trả về None
    return dict(user) if user else None

# === BOOK QUERIES ===
def get_book_by_id(book_id):
    conn = get_db()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    return dict(book) if book else None

def add_book(data):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO books (title, author, year) VALUES (?, ?, ?)',
                   (data['title'], data['author'], data['year']))
    conn.commit()
    new_book_id = cursor.lastrowid
    return get_book_by_id(new_book_id)

def update_book(book_id, data):
    conn = get_db()
    conn.execute('UPDATE books SET title = ?, author = ?, year = ? WHERE id = ?',
                   (data['title'], data['author'], data['year'], book_id))
    conn.commit()
    return get_book_by_id(book_id)

def delete_book(book_id):
    conn = get_db()
    # Tạo một đối tượng cursor từ connection
    cursor = conn.cursor()
    
    # Thực thi lệnh DELETE thông qua cursor
    cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
    
    # Commit các thay đổi vào database
    conn.commit()
    
    # Kiểm tra xem có hàng nào bị ảnh hưởng không (rowcount > 0 nghĩa là xóa thành công)
    return cursor.rowcount > 0

# === BORROW/RETURN QUERIES ===
def borrow_book(book_id, user_id):
    conn = get_db()
    try:
        with conn: # 'with': tự động commit hoặc rollback
            conn.execute("UPDATE books SET status = 'borrowed' WHERE id = ?", (book_id,))
            
            borrow_date = datetime.now().strftime("%Y-%m-%d")
            cursor = conn.cursor()
            cursor.execute('INSERT INTO borrows (book_id, user_id, borrow_date) VALUES (?, ?, ?)',
                           (book_id, user_id, borrow_date))
            
            new_borrow_id = cursor.lastrowid
            borrow_record = conn.execute('SELECT * FROM borrows WHERE borrow_id = ?', (new_borrow_id,)).fetchone()
            return dict(borrow_record)
    except conn.Error:
        return None

def return_book(book_id):
    conn = get_db()
    try:
        with conn:
            conn.execute("UPDATE books SET status = 'available' WHERE id = ?", (book_id,))
            return_date = datetime.now().strftime("%Y-%m-%d")
            res = conn.execute("UPDATE borrows SET return_date = ? WHERE book_id = ? AND return_date IS NULL",
                               (return_date, book_id))
            return res.rowcount > 0 
    except conn.Error:
        return False

# === CÁC HÀM NÂNG CAO (ĐÃ SỬA LẠI) ===

def get_borrowed_books_by_user(user_id):
    """
    Hàm cho Nesting: Lấy danh sách sách mà một người dùng đang mượn.
    """
    conn = get_db()
    query = """
        SELECT
            b.id,
            b.title,
            b.author,
            b.year,
            br.borrow_date
        FROM books AS b
        JOIN borrows AS br ON b.id = br.book_id
        WHERE br.user_id = ? AND br.return_date IS NULL
    """
    books = conn.execute(query, (user_id,)).fetchall()
    return [dict(book) for book in books]

def search_and_filter_books(search_term, author, year, page, limit):
    """
    Hàm cho Query Params: Tìm kiếm, lọc và phân trang sách.
    """
    conn = get_db()
    
    count_query = "SELECT COUNT(id) FROM books"
    base_query = "SELECT * FROM books"
    conditions = []
    params = []

    if search_term:
        conditions.append("title LIKE ?")
        params.append(f"%{search_term}%")
    if author:
        conditions.append("author = ?")
        params.append(author)
    if year:
        conditions.append("year = ?")
        params.append(year)

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        base_query += where_clause
        count_query += where_clause
    
    total_items = conn.execute(count_query, tuple(params)).fetchone()[0]
    total_pages = (total_items + limit - 1) // limit

    offset = (page - 1) * limit
    base_query += " ORDER BY id LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    results = conn.execute(base_query, tuple(params)).fetchall()
    
    return {
        "items": [dict(row) for row in results],
        "pagination": {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "limit": limit
        }
    }

def get_borrow_by_id(borrow_id):
    """Lấy thông tin một lượt mượn cụ thể bằng ID của nó."""
    conn = get_db()
    borrow = conn.execute('SELECT * FROM borrows WHERE borrow_id = ?', (borrow_id,)).fetchone()
    return dict(borrow) if borrow else None

def get_borrows_by_user_id(user_id):
    """Lấy tất cả lịch sử mượn sách của một user."""
    conn = get_db()
    borrows = conn.execute('SELECT * FROM borrows WHERE user_id = ? ORDER BY borrow_date DESC', (user_id,)).fetchall()
    return [dict(b) for b in borrows]
def get_books_cursor_paginated(limit, after_cursor=None):
    """
    Lấy danh sách sách sử dụng phương pháp phân trang bằng con trỏ (ID).
    """
    conn = get_db()

    base_query = "SELECT * FROM books"
    params = []

    # Nếu client cung cấp một 'con trỏ' (ID của cuốn sách cuối cùng họ thấy),
    # chúng ta sẽ chỉ lấy những cuốn sách có ID lớn hơn con trỏ đó.
    if after_cursor:
        base_query += " WHERE id > ?"
        params.append(after_cursor)

    # Luôn sắp xếp theo ID để đảm bảo thứ tự nhất quán
    base_query += " ORDER BY id ASC LIMIT ?"
    params.append(limit)

    results = conn.execute(base_query, tuple(params)).fetchall()

    # Xác định con trỏ cho trang tiếp theo
    next_cursor = None
    if results and len(results) == limit:
        # Nếu số lượng kết quả trả về bằng đúng limit, có khả năng còn trang sau.
        # Con trỏ tiếp theo chính là ID của cuốn sách cuối cùng trong danh sách này.
        last_book = results[-1]
        next_cursor = last_book['id']

    return {
        "items": [dict(row) for row in results],
        "next_cursor": next_cursor
    }

####### N+1 QUERY DEMO & OPTIMIZATION #######
# Thêm hàm mới này vào cuối file: library_api/queries.py

def get_borrows_for_single_user(user_id):
    """Lấy tất cả các lượt mượn cho MỘT người dùng. Sẽ được gọi trong vòng lặp."""
    conn = get_db()
    # Để đơn giản, chúng ta lấy tiêu đề sách qua JOIN
    query = """
        SELECT b.title, br.borrow_date, br.return_date
        FROM borrows as br
        JOIN books as b ON br.book_id = b.id
        WHERE br.user_id = ?
    """
    borrows = conn.execute(query, (user_id,)).fetchall()
    print(f"--- DATABASE HIT: Lấy lượt mượn cho user_id={user_id} ---") # Dòng này để debug
    return [dict(b) for b in borrows]

# Thêm hàm hiệu quả này vào file: library_api/queries.py

def get_all_users_with_borrows_optimized():
    """
    Lấy tất cả user và lịch sử mượn sách của họ một cách hiệu quả.
    Chỉ sử dụng 2 query, bất kể có bao nhiêu user.
    """
    conn = get_db()
    
    # --- Query #1: Lấy tất cả users ---
    users = conn.execute('SELECT * FROM users').fetchall()
    print("--- DATABASE HIT: Lấy tất cả users ---")
    
    if not users:
        return []

    # Chuẩn bị để xử lý bằng Python
    user_ids = [user['id'] for user in users]
    # Tạo một dictionary để dễ dàng truy cập user bằng ID
    users_by_id = {user['id']: dict(user) for user in users}
    # Thêm một list trống để chứa các lượt mượn cho mỗi user
    for user_id in users_by_id:
        users_by_id[user_id]['borrows'] = []

    # --- Query #2: Lấy TẤT CẢ các lượt mượn của TẤT CẢ các user này trong MỘT LẦN ---
    # Tạo chuỗi placeholder `(?, ?, ?)` cho mệnh đề IN
    placeholders = ', '.join(['?'] * len(user_ids))
    query = f"""
        SELECT br.user_id, b.title, br.borrow_date, br.return_date
        FROM borrows as br
        JOIN books as b ON br.book_id = b.id
        WHERE br.user_id IN ({placeholders})
    """
    all_borrows = conn.execute(query, tuple(user_ids)).fetchall()
    print(f"--- DATABASE HIT: Lấy TẤT CẢ lượt mượn cho {len(user_ids)} users ---")
    
    # --- Xử lý bằng Python (Rất nhanh) ---
    # Lặp qua danh sách các lượt mượn và "khớp" chúng vào đúng user
    for borrow in all_borrows:
        user_id = borrow['user_id']
        users_by_id[user_id]['borrows'].append(dict(borrow))
        
    # Trả về danh sách các giá trị của dictionary
    return list(users_by_id.values())
    
# === TOKEN BLACKLIST QUERIES ===

def add_jti_to_blacklist(jti):
    """Thêm một JTI (JWT ID) vào danh sách đen."""
    conn = get_db()
    try:
        conn.execute("INSERT INTO token_blacklist (jti) VALUES (?)", (jti,))
        conn.commit()
    except conn.IntegrityError:
        # JTI có thể đã tồn tại, không cần làm gì cả
        pass

def is_jti_in_blacklist(jti):
    """Kiểm tra xem một JTI có nằm trong danh sách đen không."""
    conn = get_db()
    res = conn.execute("SELECT jti FROM token_blacklist WHERE jti = ?", (jti,)).fetchone()
    return res is not None