# queries.py
from db import get_db
from datetime import datetime

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
    try:
        cursor.execute('INSERT INTO users (name, email, member_since) VALUES (?, ?, ?)',
                     (data['name'], data['email'], member_since))
        conn.commit()
        new_user_id = cursor.lastrowid
        return get_user_by_id(new_user_id)
    except conn.IntegrityError: # Bắt lỗi email bị trùng
        return None

# === BOOK QUERIES ===
def get_all_books():
    conn = get_db()
    books = conn.execute('SELECT * FROM books').fetchall()
    return [dict(book) for book in books]

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
    conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    return conn.total_changes > 0

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
            return res.rowcount > 0 # rowcount: cách chuẩn hơn để kiểm tra số dòng bị ảnh hưởng
    except conn.Error:
        return False