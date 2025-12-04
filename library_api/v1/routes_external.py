# File: library_api/v1/routes_external.py

import pybreaker
from flask import jsonify, current_app, request
from . import bp
import time

# --- CÔNG TẮC ĐIỀU KHIỂN LỖI ---
SERVICE_IS_FAILING = False

@bp.route('/external/toggle-failure', methods=['POST'])
def toggle_failure_mode():
    global SERVICE_IS_FAILING
    SERVICE_IS_FAILING = not SERVICE_IS_FAILING
    status = "FAILING" if SERVICE_IS_FAILING else "WORKING"
    current_app.logger.critical(f"--- MOCK SERVICE STATUS CHANGED TO: {status} ---")
    return jsonify({"status": status})

# --- HÀM MÔ PHỎNG VIỆC GỌI DỊCH VỤ NGOÀI ---
def call_mock_notification_service():
    """
    Hàm này sẽ ném ra Exception nếu dịch vụ giả bị lỗi.
    Đây là hành vi mà `breaker.call()` mong đợi.
    """
    if SERVICE_IS_FAILING:
        time.sleep(1)
        current_app.logger.error("External Service: Simulating a failure.")
        # Ném ra một exception để breaker.call() có thể bắt được
        raise IOError("External service is failing")
    else:
        current_app.logger.info("External Service: Notification sent successfully.")
        # Nếu thành công, trả về dữ liệu
        return {"message": "Notification sent"}

# --- ENDPOINT CHÍNH ĐƯỢC BẢO VỆ BỞI CIRCUIT BREAKER ---
@bp.route('/send-notification', methods=['POST'])
def send_notification():
    breaker = current_app.config['NOTIFICATION_BREAKER']
    current_app.logger.info(f"--- Breaker state: {breaker.current_state} ---")

    try:
        result = breaker.call(call_mock_notification_service)
        return jsonify(result), 200

    # SỬA LẠI KHỐI EXCEPT ĐỂ BẮT CẢ HAI LOẠI LỖI
    except (pybreaker.CircuitBreakerError, IOError) as e:
        current_app.logger.warning(f"Circuit Breaker action. Breaker is now '{breaker.current_state}'. Reason: {e}")
        return jsonify({
            "error": "ServiceUnavailable",
            "message": "The notification service is temporarily unavailable. Please try again later."
        }), 503