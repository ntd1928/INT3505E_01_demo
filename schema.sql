-- schema.sql

-- Xóa các bảng nếu chúng đã tồn tại để đảm bảo khởi tạo lại từ đầu
DROP TABLE IF EXISTS borrows;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS users;

-- Bảng lưu trữ thông tin người dùng
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    member_since TEXT NOT NULL
);

-- Bảng lưu trữ thông tin sách
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available', 'borrowed'))
);

-- Bảng lưu trữ lịch sử mượn/trả sách
CREATE TABLE borrows (
    borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    borrow_date TEXT NOT NULL,
    return_date TEXT,
    FOREIGN KEY (book_id) REFERENCES books (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);