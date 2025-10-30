# File: library_api/db.py

import sqlite3
import os
from flask import g, current_app, cli
from datetime import datetime
from werkzeug.security import generate_password_hash

def get_db():
    """
    Tạo hoặc tái sử dụng kết nối CSDL trong cùng một request.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """
    Đóng kết nối CSDL khi request kết thúc.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """
    Thực thi file schema.sql và thêm dữ liệu mẫu.
    """
    db = get_db()
    
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf8") as f:
        db.executescript(f.read())

    cursor = db.cursor()
    
    try:
        cursor.execute("INSERT INTO users (id, name, email, password, member_since) VALUES (?, ?, ?, ?, ?)",
            (1, 'Alice', 'alice@example.com', generate_password_hash('alice123'), datetime.now().strftime("%Y-%m-%d"))
        )
        cursor.execute("INSERT INTO users (id, name, email, password, member_since) VALUES (?, ?, ?, ?, ?)",
            (2, 'Bob', 'bob@example.com', generate_password_hash('bob456'), datetime.now().strftime("%Y-%m-%d"))
        )
        db.commit()
        print("Added sample users.")
    except db.IntegrityError:
        print("Sample users might already exist.")
        db.rollback()

    try:
        cursor.execute("INSERT INTO books (id, title, author, year, status) VALUES (?, ?, ?, ?, ?)",
            (1, 'Lão Hạc', 'Nam Cao', 1943, 'available')
        )
        cursor.execute("INSERT INTO books (id, title, author, year, status) VALUES (?, ?, ?, ?, ?)",
            (2, 'Số Đỏ', 'Vũ Trọng Phụng', 1936, 'available')
        )
        cursor.execute("INSERT INTO books (id, title, author, year, status) VALUES (?, ?, ?, ?, ?)",
            (3, 'Dế Mèn Phiêu Lưu Ký', 'Tô Hoài', 1941, 'borrowed')
        )
        db.commit()
        print("Added sample books.")
    except db.IntegrityError:
        print("Sample books might already exist.")
        db.rollback()

    try:
        cursor.execute("INSERT INTO borrows (book_id, user_id, borrow_date) VALUES (?, ?, ?)",
            (3, 1, '2023-10-26')
        )
        db.commit()
        print("Added sample borrow records.")
    except db.IntegrityError:
        print("Sample borrow records might already exist.")
        db.rollback()

def init_app(app):
    """
    Hàm đăng ký các chức năng quản lý DB với ứng dụng Flask.
    """
    # Đăng ký hàm close_db để được gọi sau mỗi request
    app.teardown_appcontext(close_db)
    
    # Thêm lệnh 'init-db' vào Flask CLI
    @app.cli.command('init-db')
    def init_db_command():
        """Xóa dữ liệu cũ, tạo bảng mới và thêm dữ liệu mẫu."""
        with app.app_context():
            init_db()
