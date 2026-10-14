-- 1. All books.
SELECT book_id, title, author, category FROM books ORDER BY book_id;

-- 2. Filter a category.
SELECT * FROM books WHERE category = 'Công nghệ';

-- 3. Joined loan history.
SELECT l.loan_id, b.title, c.copy_code, m.name, l.borrowed_on, l.due_on, l.returned_on
FROM loans l JOIN book_copies c ON c.copy_id=l.copy_id
JOIN books b ON b.book_id=c.book_id JOIN members m ON m.member_id=l.member_id
ORDER BY l.loan_id;

-- 4. Include books with no loans: COUNT(l.loan_id), not COUNT(*).
SELECT b.book_id,b.title,COUNT(l.loan_id) AS loan_count
FROM books b LEFT JOIN book_copies c ON c.book_id=b.book_id
LEFT JOIN loans l ON l.copy_id=c.copy_id
GROUP BY b.book_id,b.title ORDER BY loan_count DESC,b.book_id;

-- 5. Available physical copies.
SELECT c.copy_id,c.copy_code FROM book_copies c
WHERE NOT EXISTS (SELECT 1 FROM loans l WHERE l.copy_id=c.copy_id AND l.returned_on IS NULL);

-- 6. Overdue on the SAMPLE reference date.
SELECT * FROM loans WHERE returned_on IS NULL AND due_on < '2025-12-31';

-- 7. Monthly loans.
SELECT strftime('%Y-%m',borrowed_on) AS month,COUNT(*) AS loan_count
FROM loans GROUP BY month ORDER BY month;

-- 8. Duration: returned loans only.
SELECT loan_id,CAST(julianday(returned_on)-julianday(borrowed_on) AS INTEGER) AS duration_days
FROM loans WHERE returned_on IS NOT NULL;

-- 9. Reader activity, including readers with zero loans.
SELECT m.member_id,m.name,COUNT(l.loan_id) AS loan_count
FROM members m LEFT JOIN loans l ON l.member_id=m.member_id
GROUP BY m.member_id,m.name ORDER BY loan_count DESC,m.member_id;
