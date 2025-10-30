-- Xóa các bảng cũ nếu chúng tồn tại, để đảm bảo khởi tạo lại từ đầu
DROP TABLE IF EXISTS borrows;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS token_blacklist;

-- Tạo bảng users
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  member_since TEXT NOT NULL
);

-- Tạo bảng books
CREATE TABLE books (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  author TEXT NOT NULL,
  year INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'available'
);

-- Tạo bảng borrows
CREATE TABLE borrows (
  borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  borrow_date TEXT NOT NULL,
  return_date TEXT,
  FOREIGN KEY (book_id) REFERENCES books (id),
  FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Bảng để lưu các token đã bị thu hồi (blacklist)
CREATE TABLE token_blacklist (
  jti TEXT PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);