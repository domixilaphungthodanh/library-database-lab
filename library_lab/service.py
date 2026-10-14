"""Business operations shared by CLI, notebooks and tests."""
from datetime import date, timedelta
import sqlite3
from .db import DEFAULT_DB, connect, iso_day, required, today


def add_book(title, author, category, db=DEFAULT_DB):
    values = [required(title, 'Tên sách'), required(author, 'Tác giả'), required(category, 'Danh mục')]
    with connect(db) as conn, conn:
        return conn.execute('INSERT INTO books(title,author,category) VALUES (?,?,?)', values).lastrowid


def add_copy(book_id, copy_code, db=DEFAULT_DB):
    code = required(copy_code, 'Mã cuốn')
    with connect(db) as conn, conn:
        if not conn.execute('SELECT 1 FROM books WHERE book_id=?', (book_id,)).fetchone():
            raise ValueError('Đầu sách không tồn tại.')
        try:
            return conn.execute('INSERT INTO book_copies(book_id,copy_code) VALUES (?,?)', (book_id, code)).lastrowid
        except sqlite3.IntegrityError:
            raise ValueError('Mã cuốn đã tồn tại.') from None


def add_member(name, email=None, db=DEFAULT_DB):
    name = required(name, 'Tên độc giả')
    email = (email or '').strip().lower() or None
    with connect(db) as conn, conn:
        try:
            return conn.execute('INSERT INTO members(name,email) VALUES (?,?)', (name, email)).lastrowid
        except sqlite3.IntegrityError:
            raise ValueError('Email đã được đăng ký.') from None


def borrow(copy_id, member_id, borrowed_on=None, db=DEFAULT_DB):
    day = iso_day(borrowed_on if borrowed_on is not None else today())
    if date.fromisoformat(day) > today():
        raise ValueError('Ngày mượn không được ở tương lai.')
    try:
        due = (date.fromisoformat(day) + timedelta(days=14)).isoformat()
    except OverflowError:
        raise ValueError('Ngày mượn vượt phạm vi hỗ trợ.') from None
    with connect(db) as conn:
        conn.execute('BEGIN IMMEDIATE')
        with conn:
            if not conn.execute('SELECT 1 FROM book_copies WHERE copy_id=?', (copy_id,)).fetchone():
                raise ValueError('Bản sao sách không tồn tại.')
            if not conn.execute('SELECT 1 FROM members WHERE member_id=?', (member_id,)).fetchone():
                raise ValueError('Độc giả không tồn tại.')
            try:
                return conn.execute('INSERT INTO loans(copy_id,member_id,borrowed_on,due_on) VALUES (?,?,?,?)', (copy_id, member_id, day, due)).lastrowid
            except sqlite3.IntegrityError:
                raise ValueError('Cuốn sách đang được mượn hoặc ngày mượn chồng lên lịch sử trước đó.') from None


def return_book(loan_id, returned_on=None, db=DEFAULT_DB):
    day = iso_day(returned_on if returned_on is not None else today())
    if date.fromisoformat(day) > today():
        raise ValueError('Ngày trả không được ở tương lai.')
    with connect(db) as conn:
        conn.execute('BEGIN IMMEDIATE')
        with conn:
            loan = conn.execute('SELECT * FROM loans WHERE loan_id=?', (loan_id,)).fetchone()
            if loan is None:
                raise ValueError('Lượt mượn không tồn tại.')
            if loan['returned_on'] is not None:
                raise ValueError('Lượt mượn này đã trả.')
            if day < loan['borrowed_on']:
                raise ValueError('Ngày trả không được trước ngày mượn.')
            conn.execute('UPDATE loans SET returned_on=? WHERE loan_id=?', (day, loan_id))


def search_books(keyword='', db=DEFAULT_DB):
    # Treat %, _ and backslash as literal user text rather than LIKE wildcards.
    value = keyword.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    query = """SELECT b.*, COUNT(c.copy_id) AS total_copies,
    SUM(CASE WHEN c.copy_id IS NOT NULL AND l.loan_id IS NULL THEN 1 ELSE 0 END) AS available_copies
    FROM books b LEFT JOIN book_copies c ON c.book_id=b.book_id
    LEFT JOIN loans l ON l.copy_id=c.copy_id AND l.returned_on IS NULL
    WHERE b.title LIKE ? ESCAPE '\\' OR b.author LIKE ? ESCAPE '\\' OR b.category LIKE ? ESCAPE '\\'
    GROUP BY b.book_id ORDER BY b.book_id"""
    with connect(db, readonly=True) as conn:
        return [dict(row) for row in conn.execute(query, (f'%{value}%',) * 3)]


def list_members(db=DEFAULT_DB):
    with connect(db, readonly=True) as conn:
        return [dict(row) for row in conn.execute('SELECT * FROM members ORDER BY member_id')]


def available_copies(db=DEFAULT_DB):
    with connect(db, readonly=True) as conn:
        return [dict(row) for row in conn.execute('''SELECT c.copy_id,c.copy_code,b.title
        FROM book_copies c JOIN books b ON b.book_id=c.book_id
        WHERE NOT EXISTS (SELECT 1 FROM loans l WHERE l.copy_id=c.copy_id AND l.returned_on IS NULL)
        ORDER BY c.copy_id''')]


def active_loans(db=DEFAULT_DB, overdue_only=False, as_of=None):
    day = iso_day(as_of if as_of is not None else today())
    query = '''SELECT l.*, c.copy_code,b.title,m.name,
    CASE WHEN l.due_on < ? THEN 1 ELSE 0 END AS overdue
    FROM loans l JOIN book_copies c ON c.copy_id=l.copy_id
    JOIN books b ON b.book_id=c.book_id JOIN members m ON m.member_id=l.member_id
    WHERE l.returned_on IS NULL'''
    params = [day]
    if overdue_only:
        query += ' AND l.due_on < ?'
        params.append(day)
    with connect(db, readonly=True) as conn:
        return [dict(row) for row in conn.execute(query + ' ORDER BY l.due_on,l.loan_id', params)]
