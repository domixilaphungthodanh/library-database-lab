# Từ điển dữ liệu

Mã INTEGER PRIMARY KEY được SQLite cấp khi thêm dữ liệu. Tất cả trường trừ email và ngày trả đều bắt buộc. Ngày là TEXT theo ISO `YYYY-MM-DD`.

| Bảng | Cột | Ý nghĩa / ràng buộc |
|---|---|---|
| books | book_id | Khóa chính đầu sách |
| books | title | Tên đầu sách, không rỗng |
| books | author | Tác giả; v1 lưu một chuỗi, không tách bảng tác giả |
| books | category | Danh mục, không rỗng |
| book_copies | copy_id | Khóa chính cuốn vật lý |
| book_copies | book_id | Khóa ngoại đến books |
| book_copies | copy_code | Mã cuốn duy nhất, không rỗng, phân biệt hoa/thường |
| members | member_id | Khóa chính độc giả |
| members | name | Tên độc giả, không rỗng |
| members | email | Tùy chọn; NULL nếu bỏ trống; duy nhất khi nhập |
| loans | loan_id | Khóa chính lượt mượn |
| loans | copy_id | Khóa ngoại đến book_copies |
| loans | member_id | Khóa ngoại đến members |
| loans | borrowed_on | Ngày mượn hợp lệ |
| loans | due_on | Hạn trả hợp lệ, không trước ngày mượn; service đặt sau 14 ngày |
| loans | returned_on | NULL = đang mượn; nếu có, phải hợp lệ và không trước ngày mượn |

## Những khái niệm cần biết

- Khóa chính: nhận diện duy nhất một dòng.
- Khóa ngoại: ngăn tham chiếu đến sách/độc giả không tồn tại.
- Index: giúp tìm kiếm và có thể bảo vệ tính duy nhất. Partial unique index `one_open_loan_per_copy` chỉ áp dụng khi `returned_on IS NULL`.
- Trigger: kiểm tra lịch sử mượn không chồng nhau khi INSERT/UPDATE.
- Transaction: các bước liên quan được lưu cùng nhau, lỗi thì rollback.
- NULL: chưa có dữ liệu, không phải chuỗi rỗng hoặc số 0. SQL dùng `IS NULL`, không dùng `= NULL`.

Đếm lượt mượn: đếm dòng loans. Đếm đầu sách: đếm books. Đếm cuốn vật lý: đếm book_copies. Đếm người mượn duy nhất: COUNT(DISTINCT member_id). Các đại lượng không thay thế cho nhau.
