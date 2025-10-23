# run.py

from library_api import create_app

# Tạo instance của ứng dụng từ factory
app = create_app()

if __name__ == '__main__':
    # Chạy app ở chế độ debug
    # Trong môi trường production, bạn nên dùng một WSGI server như Gunicorn hoặc Waitress
    app.run(debug=True, port=5001)