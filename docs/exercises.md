# Bài tập theo tuần

Mỗi bài: viết câu hỏi, truy vấn/mã, kiểm tra kết quả và một câu giải thích. Dùng mẫu trước khi thêm dữ liệu riêng; ngày mẫu 2025-12-31.

## Tuần 1 — Thiết kế và SQL

1. Đếm đầu sách, bản sao, độc giả, lượt mượn. Vì sao đầu sách và bản sao cần hai bảng?
2. Lọc đầu sách danh mục Công nghệ. Tìm sách theo tên tác giả bằng tham số trong Python.
3. JOIN bốn bảng để xem ai mượn cuốn nào, tên sách và hạn trả.
4. Đếm lượt mượn theo đầu sách, kể cả đầu sách chưa được mượn. Vì sao không dùng COUNT(*) với LEFT JOIN?

## Tuần 2 — Quy tắc và transaction

5. Tự tạo đầu sách, bản sao và độc giả bằng menu. Mượn rồi trả; ghi lại các mã khác nhau.
6. Thử mượn cuốn đang có người mượn, nhập mã không tồn tại và trả hai lần. Kiểm tra số lượt không tăng khi lỗi.
7. Viết truy vấn bản sao còn sẵn và lượt quá hạn tại ngày mẫu. Giải thích `IS NULL` và `<`.
8. Giải thích transaction, khóa ngoại, partial unique index và trigger bằng ví dụ trong dự án.

## Tuần 3 — Phân tích

9. Tính lượt mượn theo tháng bằng SQL và pandas; đối chiếu tổng với loans.
10. Tính thời gian mượn của các lượt đã trả; so sánh mean và median bằng histogram.
11. Tính tỷ lệ trả trễ trong các lượt đã trả; phân biệt với số lượt đang quá hạn.
12. Viết ba nhận xét có số liệu, hai câu hỏi cần dữ liệu thật và giới hạn. Không kết luận nhu cầu đọc từ mẫu ngẫu nhiên.

Lời giải ở `solutions.md`; nên thử làm trước.
