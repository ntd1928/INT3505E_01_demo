# db.py
import sqlite3
import os
from flask import g
from datetime import datetime

DATABASE = "library.db"

def get_db():
    """
    Tạo hoặc tái sử dụng kết nối CSDL trong cùng một request.
    """
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """
    Đóng kết nối CSDL khi request kết thúc.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db(app):
    """
    Thực thi file schema.sql và thêm dữ liệu mẫu.
    """
    with app.app_context():
        db = get_db()
        
        # 1. Tạo bảng từ schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r", encoding="utf8") as f:
            db.executescript(f.read())

        # 2. Thêm dữ liệu mẫu (Seeding)
        cursor = db.cursor()
        
        # Thêm users
        cursor.execute("INSERT INTO users (name, email, member_since) VALUES (?, ?, ?)",
            ('Nguyễn Văn A', 'nva@example.com', datetime.now().strftime("%Y-%m-%d"))
        )
        cursor.execute("INSERT INTO users (name, email, member_since) VALUES (?, ?, ?)",
            ('Trần Thị B', 'ttb@example.com', datetime.now().strftime("%Y-%m-%d"))
        )

        # Thêm books
        cursor.execute("INSERT INTO books (title, author, year, status) VALUES (?, ?, ?, ?)",
            ('Lão Hạc', 'Nam Cao', 1943, 'available')
        )
        cursor.execute("INSERT INTO books (title, author, year, status) VALUES (?, ?, ?, ?)",
            ('Số Đỏ', 'Vũ Trọng Phụng', 1936, 'available')
        )
        cursor.execute("INSERT INTO books (title, author, year, status) VALUES (?, ?, ?, ?)",
            ('Dế Mèn Phiêu Lưu Ký', 'Tô Hoài', 1941, 'borrowed')
        )

        # Thêm borrows
        cursor.execute("INSERT INTO borrows (book_id, user_id, borrow_date) VALUES (?, ?, ?)",
            (3, 1, '2023-10-26')
        )
        
        db.commit()

def init_app(app):
    """
    Hàm đăng ký các chức năng quản lý DB với ứng dụng Flask.
    """
    app.teardown_appcontext(close_db)
    
    @app.cli.command('init-db')
    def init_db_command():
        """Xóa dữ liệu cũ, tạo bảng mới và thêm dữ liệu mẫu."""
        init_db(app)
        print('Initialized the database with schema and sample data.')