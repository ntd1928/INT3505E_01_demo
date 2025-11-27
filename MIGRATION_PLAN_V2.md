# Kế Hoạch Nâng Cấp API PayNow: Di Chuyển Từ v1 Lên v2

**Ngày công bố:** 01/01/2026

**Đối tượng:** Các nhà phát triển đang tích hợp API Thanh toán PayNow v1.

---

Chào các nhà phát triển,

Để tăng cường bảo mật, tuân thủ tiêu chuẩn PCI DSS và mang lại những tính năng mạnh mẽ hơn cho nền tảng của bạn, PayNow sẽ chính thức ra mắt phiên bản API v2. Phiên bản v1 sẽ được ngừng hỗ trợ theo lộ trình chi tiết bên dưới.

Tài liệu này sẽ hướng dẫn bạn qua các bước cần thiết để nâng cấp hệ thống của mình một cách suôn sẻ và an toàn.

### 1. Tại Sao Cần Nâng Cấp Lên v2?

Việc nâng cấp không chỉ là một yêu cầu kỹ thuật mà còn mang lại những lợi ích kinh doanh và bảo mật cốt lõi:

-   **Bảo mật Tối Đa (PCI DSS Compliant):** Luồng thanh toán của v2 sử dụng `payment_token`, giúp hệ thống của bạn không cần phải xử lý hoặc lưu trữ trực tiếp thông tin thẻ nhạy cảm của khách hàng, giảm thiểu đáng kể rủi ro và trách nhiệm pháp lý.
-   **Chính Xác Tuyệt Đối:** Trường `amount` giờ đây được tính bằng đơn vị tiền tệ nhỏ nhất (ví dụ: cents cho USD, đồng cho VND), tránh hoàn toàn các lỗi làm tròn số thập phân có thể gây thất thoát tài chính.
-   **Linh Hoạt Hơn:** Giới thiệu trường `metadata` cho phép bạn lưu trữ các thông tin tùy chỉnh (như `order_id`, `customer_id`) liên quan đến giao dịch, giúp việc đối soát và quản lý trở nên dễ dàng hơn.

### 2. Bảng Phân Tích Thay Đổi Chi Tiết (Changelog)

| Thành phần          | Phiên bản v1 (`POST /v1/charge`)     | Phiên bản v2 (`POST /v2/charges`) (Thay đổi)              | Mức độ       |
|:--------------------|:-------------------------------------|:----------------------------------------------------------|:-------------|
| **Endpoint**        | `/v1/charge`                         | `/v2/charges` (số nhiều)                                  | **Breaking** |
| **Trường `amount`**     | `float` (ví dụ: `100.50`)            | `integer` (ví dụ: `10050` cho $100.50)                     | **Breaking** |
| **Trường `card_number`**| Bắt buộc, `string`                 | **Đã Xóa**. Thay thế bằng `payment_token`                 | **Breaking** |
| **Trường `expiry_month`**| Bắt buộc, `integer`                | **Đã Xóa**                                                | **Breaking** |
| **Trường `expiry_year`** | Bắt buộc, `integer`                | **Đã Xóa**                                                | **Breaking** |
| **Trường `cvc`**         | Bắt buộc, `string`                 | **Đã Xóa**                                                | **Breaking** |
| **Trường `description`**| `string`                             | **Đã Xóa**. Chuyển vào `metadata.description`             | **Breaking** |
| **Trường `payment_token`**| Không có                           | Bắt buộc, `string`                                        | **Mới**      |
| **Trường `metadata`**    | Không có                           | Không bắt buộc, `object`                                  | **Mới**      |

### 3. Hướng Dẫn Nâng Cấp Kỹ Thuật

Luồng thanh toán mới sẽ bao gồm 2 bước:

1.  **(Phía Frontend)** Sử dụng thư viện `PayNow.js` của chúng tôi để tạo `payment_token` từ form thanh toán của bạn một cách an toàn phía client.
2.  **(Phía Backend)** Gửi `payment_token` đó (thay vì toàn bộ chi tiết thẻ) đến API `POST /v2/charges` để thực hiện thanh toán.

#### Ví dụ Code Backend (Node.js):

**Trước (v1):**

```javascript
// WARNING: Deprecated method
const charge = await paynow.charges.create({
  amount: 100.50,
  currency: 'usd',
  card_number: req.body.cardNumber,
  expiry_month: req.body.expMonth,
  expiry_year: req.body.expYear,
  cvc: req.body.cvc
});
```

**Sau (v2):**

```javascript
// payment_token được gửi an toàn từ frontend
const { payment_token, orderId } = req.body;

const charge = await paynow.charges.create({
  amount: 10050, // Luôn là số nguyên
  currency: 'usd',
  payment_token: payment_token,
  metadata: { 
    order_id: orderId,
    description: 'T-shirt purchase' 
  }
});
```

---


### 4. Lộ Trình Ngừng Hỗ Trợ v1

Chúng tôi cam kết cung cấp đủ thời gian để bạn thực hiện nâng cấp.

-   **01/01/2026:** API v2 chính thức phát hành. API v1 bước vào giai đoạn **deprecated**. Các header cảnh báo sẽ được thêm vào response của v1.
-   **01/07/2026:** Bắt đầu giai đoạn **"brownout"**. Chúng tôi sẽ tạm thời ngắt API v1 trong 2 giờ (02:00-04:00 UTC) vào ngày đầu tiên của mỗi tháng để nhắc nhở và giúp bạn phát hiện các tích hợp còn sót lại.
-   **31/12/2026:** **"Sunset"**. API v1 sẽ ngừng hoạt động vĩnh viễn. Tất cả các request đến `/v1/charge` sẽ nhận lỗi `410 Gone`.

### 5. Hỗ Trợ

Chúng tôi hiểu rằng quá trình nâng cấp có thể phát sinh vấn đề. Vui lòng liên hệ với chúng tôi qua các kênh sau:

-   **Tài liệu kỹ thuật v2:** [docs.paynow.example.com/v2](https://docs.paynow.example.com/v2)
-   **Báo cáo lỗi hoặc đặt câu hỏi:** [GitHub Issues](https://github.com/paynow/api-support)
-   **Hỗ trợ trực tiếp:** support@paynow.example.com

Chúng tôi đánh giá cao sự hợp tác của bạn trong việc xây dựng một hệ sinh thái thanh toán an toàn và hiện đại hơn.

Trân trọng,
**Đội ngũ Kỹ thuật PayNow**

---