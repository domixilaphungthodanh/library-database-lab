CREATE TABLE books (
 book_id INTEGER PRIMARY KEY,
 title TEXT NOT NULL CHECK(length(trim(title)) > 0),
 author TEXT NOT NULL CHECK(length(trim(author)) > 0),
 category TEXT NOT NULL CHECK(length(trim(category)) > 0)
);
CREATE TABLE book_copies (
 copy_id INTEGER PRIMARY KEY,
 book_id INTEGER NOT NULL REFERENCES books(book_id),
 copy_code TEXT NOT NULL UNIQUE CHECK(length(trim(copy_code)) > 0)
);
CREATE TABLE members (
 member_id INTEGER PRIMARY KEY,
 name TEXT NOT NULL CHECK(length(trim(name)) > 0),
 email TEXT UNIQUE CHECK(email IS NULL OR length(trim(email)) > 0)
);
CREATE TABLE loans (
 loan_id INTEGER PRIMARY KEY,
 copy_id INTEGER NOT NULL REFERENCES book_copies(copy_id),
 member_id INTEGER NOT NULL REFERENCES members(member_id),
 borrowed_on TEXT NOT NULL CHECK(borrowed_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(borrowed_on, '+0 days') IS NOT NULL AND date(borrowed_on, '+0 days') = borrowed_on),
 due_on TEXT NOT NULL CHECK(due_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(due_on, '+0 days') IS NOT NULL AND date(due_on, '+0 days') = due_on AND due_on >= borrowed_on),
 returned_on TEXT CHECK(returned_on IS NULL OR (returned_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(returned_on, '+0 days') IS NOT NULL AND date(returned_on, '+0 days') = returned_on AND returned_on >= borrowed_on))
);
CREATE UNIQUE INDEX one_open_loan_per_copy ON loans(copy_id) WHERE returned_on IS NULL;
CREATE INDEX loans_member ON loans(member_id);
CREATE INDEX loans_borrowed ON loans(borrowed_on);
-- Closed intervals include the return day. Next borrowing is allowed next day.
CREATE TRIGGER prevent_loan_overlap_insert BEFORE INSERT ON loans
WHEN EXISTS (
 SELECT 1 FROM loans l WHERE l.copy_id = NEW.copy_id
 AND NEW.borrowed_on <= COALESCE(l.returned_on, '9999-12-31')
 AND l.borrowed_on <= COALESCE(NEW.returned_on, '9999-12-31')
)
BEGIN SELECT RAISE(ABORT, 'Overlapping loans for this copy'); END;
CREATE TRIGGER prevent_loan_overlap_update BEFORE UPDATE ON loans
WHEN EXISTS (
 SELECT 1 FROM loans l WHERE l.copy_id = NEW.copy_id AND l.loan_id != NEW.loan_id
 AND NEW.borrowed_on <= COALESCE(l.returned_on, '9999-12-31')
 AND l.borrowed_on <= COALESCE(NEW.returned_on, '9999-12-31')
)
BEGIN SELECT RAISE(ABORT, 'Overlapping loans for this copy'); END;
