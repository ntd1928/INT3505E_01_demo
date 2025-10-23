# File: library_api/db.py

import sqlite3
import os
from flask import g, current_app # Import thêm current_app
from datetime import datetime

def get_db():
    """
    Tạo hoặc tái sử dụng kết nối CSDL trong cùng một request.
    Lấy đường dẫn DB từ config của ứng dụng.
    """
    if "db" not in g:
        # THAY ĐỔI QUAN TRỌNG: Lấy đường dẫn từ app config, không dùng biến toàn cục
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

def init_db(): # Sửa lại: Không cần truyền 'app' vào đây nữa
    """
    Thực thi file schema.sql và thêm dữ liệu mẫu.
    Hàm này sẽ được gọi bởi lệnh CLI, nơi app_context đã tồn tại.
    """
    db = get_db()
    
    # 1. Tạo bảng từ schema.sql
    # Lấy đường dẫn schema.sql từ thư mục hiện tại của file db.py
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf8") as f:
        db.executescript(f.read())

    # 2. Thêm dữ liệu mẫu (Seeding)
    cursor = db.cursor()
    
    # Thêm users
    try:
        cursor.execute("INSERT INTO users (id, name, email, member_since) VALUES (?, ?, ?, ?)",
            (1, 'Alice', 'alice@example.com', datetime.now().strftime("%Y-%m-%d"))
        )
        cursor.execute("INSERT INTO users (id, name, email, member_since) VALUES (?, ?, ?, ?)",
            (2, 'Bob', 'bob@example.com', datetime.now().strftime("%Y-%m-%d"))
        )

        # Thêm books
        cursor.execute("INSERT INTO books (id, title, author, year, status) VALUES (?, ?, ?, ?, ?)",
            (1, 'Lão Hạc', 'Nam Cao', 1943, 'available')
        )
        cursor.execute("INSERT INTO books (id, title, author, year, status) VALUES (?, ?, ?, ?, ?)",
            (2, 'Số Đỏ', 'Vũ Trọng Phụng', 1936, 'available')
        )
        cursor.execute("INSERT INTO books (id, title, author, year, status) VALUES (?, ?, ?, ?, ?)",
            (3, 'Dế Mèn Phiêu Lưu Ký', 'Tô Hoài', 1941, 'borrowed')
        )

        # Thêm borrows
        cursor.execute("INSERT INTO borrows (book_id, user_id, borrow_date) VALUES (?, ?, ?)",
            (3, 1, '2023-10-26')
        )
        
        db.commit()
    except db.IntegrityError:
        # Dữ liệu có thể đã tồn tại, không cần làm gì cả
        print("Sample data might already exist.")
        pass

def init_app(app):
    """
    Hàm đăng ký các chức năng quản lý DB với ứng dụng Flask.
    """
    app.teardown_appcontext(close_db)
    
    @app.cli.command('init-db')
    def init_db_command():
        """Xóa dữ liệu cũ, tạo bảng mới và thêm dữ liệu mẫu."""
        # Gọi hàm init_db trực tiếp
        init_db()
        print('Initialized the database with schema and sample data.')