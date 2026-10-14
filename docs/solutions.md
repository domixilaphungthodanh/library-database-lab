# Lời giải tham khảo

## 1–4: Dữ liệu và JOIN

Mẫu có 20 đầu sách, 40 bản sao, 30 độc giả, 150 lượt mượn. books lưu tác phẩm; book_copies lưu từng cuốn vật lý có thể được mượn riêng. Xem truy vấn 1–4 trong `sql/analysis.sql`.

Python tìm tác giả có tham số:

```python
from library_lab.db import connect
with connect(readonly=True) as conn:
    rows = conn.execute('SELECT * FROM books WHERE author = ?', ('Tác giả 01',)).fetchall()
```

LEFT JOIN giữ đầu sách chưa có lượt mượn; COUNT(l.loan_id) chỉ đếm mã lượt không NULL, còn COUNT(*) đếm cả dòng giữ lại đó.

## 5–8: Thao tác và ràng buộc

Theo quy trình README. book_id là đầu sách, copy_id là cuốn, member_id là người, loan_id là lần mượn. Chọn một bản sao còn sẵn thay vì mã đầu sách khi mượn.

Các lỗi phải được báo và không thêm lượt; tests/test_library.py kiểm tra số dòng sau lỗi. Ngày trả sớm hơn ngày mượn bị từ chối; lượt đã trả không thể trả lại.

Truy vấn 5–6 tìm còn sẵn và quá hạn. Mẫu ban đầu có 20 bản sao còn sẵn, 20 lượt đang mượn, 10 lượt quá hạn tại 2025-12-31. `returned_on IS NULL` nghĩa là chưa trả. Dùng `<` để hạn trả bằng ngày tham chiếu vẫn đúng hạn.

Khóa ngoại bảo vệ liên kết, partial unique index bảo vệ một lượt chưa trả/cuốn, trigger ngăn khoảng lịch sử chồng nhau. Transaction mượn dùng BEGIN IMMEDIATE để giữ quyền ghi trước khi kiểm tra; lỗi thì rollback.

## 9: Đối chiếu SQL và pandas

```python
from library_lab.analyze import load_tables
tables = load_tables()
assert len(tables['loans']) == tables['monthly']['loan_count'].sum()
```

Truy vấn tháng nằm ở mục 7 của `sql/analysis.sql`; tháng không có lượt giữa tháng đầu và cuối được pandas thêm với giá trị 0.

## 10: Thời gian mượn

```python
returned = tables['returned']
print(returned['duration_days'].mean(), returned['duration_days'].median())
```

Có 130 lượt đã trả trong mẫu. Công thức: ngày trả − ngày mượn, tính theo ngày lịch. Histogram cho thấy phân phối; mean nhạy hơn với lượt kéo dài. Không gán 0 cho lượt chưa trả.

## 11: Tỷ lệ trả trễ

```sql
SELECT COUNT(*) AS returned_loans,
       SUM(CASE WHEN returned_on > due_on THEN 1 ELSE 0 END) AS late_returns,
       100.0 * SUM(CASE WHEN returned_on > due_on THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0) AS late_pct
FROM loans WHERE returned_on IS NOT NULL;
```

Mẫu số là lượt đã trả; không phải toàn bộ lượt. Lượt đang quá hạn là chỉ số khác, phụ thuộc ngày tham chiếu.

## 12: Báo cáo

Đọc outputs/report.md sau khi chạy phân tích, đối chiếu CSV và biểu đồ. Nếu có đồng hạng, không tuyên bố một đầu sách là người dẫn đầu duy nhất. Đề xuất câu hỏi cần dữ liệu thật: số bản sao có làm tăng lượt mượn không; độc giả có nhu cầu gì chưa được đáp ứng? Mẫu giả lập không chứng minh hai điều đó.
