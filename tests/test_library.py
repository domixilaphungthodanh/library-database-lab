import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from library_lab.init_db import initialize
from library_lab.db import connect, iso_day
from library_lab import service


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'library.db'
        initialize(self.db)
        self.book = service.add_book('Python', 'Tác giả', 'Công nghệ', self.db)
        self.copy = service.add_copy(self.book, 'COPY-1', self.db)
        self.member = service.add_member('Độc giả', db=self.db)

    def test_borrow_return_and_availability(self):
        loan = service.borrow(self.copy, self.member, '2025-01-01', self.db)
        self.assertEqual(service.available_copies(self.db), [])
        self.assertEqual(service.active_loans(self.db)[0]['due_on'], '2025-01-15')
        service.return_book(loan, '2025-01-15', self.db)
        self.assertEqual(len(service.available_copies(self.db)), 1)
        self.assertEqual(service.active_loans(self.db), [])

    def test_double_borrow_and_missing_ids_are_atomic(self):
        service.borrow(self.copy, self.member, '2025-01-01', self.db)
        for copy_id, member_id in [(self.copy, self.member), (999, self.member), (self.copy, 999)]:
            with self.assertRaises(ValueError):
                service.borrow(copy_id, member_id, '2025-01-02', self.db)
        with connect(self.db) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM loans').fetchone()[0], 1)

    def test_invalid_returns_and_missing_loan(self):
        loan = service.borrow(self.copy, self.member, '2025-01-02', self.db)
        with self.assertRaises(ValueError):
            service.return_book(loan, '2025-01-01', self.db)
        self.assertEqual(len(service.active_loans(self.db)), 1)
        with self.assertRaises(ValueError):
            service.return_book(999, '2025-01-03', self.db)
        service.return_book(loan, '2025-01-03', self.db)
        with self.assertRaises(ValueError):
            service.return_book(loan, '2025-01-04', self.db)

    def test_overdue_boundary_and_returned_exclusion(self):
        loan = service.borrow(self.copy, self.member, '2025-01-01', self.db)
        self.assertEqual(service.active_loans(self.db, True, '2025-01-15'), [])
        self.assertEqual(len(service.active_loans(self.db, True, '2025-01-16')), 1)
        service.return_book(loan, '2025-01-16', self.db)
        self.assertEqual(service.active_loans(self.db, True, '2025-01-17'), [])

    def test_copy_email_and_required_fields(self):
        with self.assertRaises(ValueError):
            service.add_copy(self.book, 'COPY-1', self.db)
        with self.assertRaises(ValueError):
            service.add_copy(999, 'COPY-2', self.db)
        for field in [(' ', 'A', 'B'), ('A', ' ', 'B'), ('A', 'B', ' ')]:
            with self.assertRaises(ValueError):
                service.add_book(*field, db=self.db)
        with self.assertRaises(ValueError):
            service.add_member(' ', db=self.db)
        service.add_member('A', ' A@example.com ', self.db)
        with self.assertRaises(ValueError):
            service.add_member('B', 'a@EXAMPLE.COM', self.db)
        service.add_member('C', '', self.db)

    def test_database_foreign_keys_dates_and_overlap(self):
        with connect(self.db) as conn:
            self.assertEqual(conn.execute('PRAGMA foreign_keys').fetchone()[0], 1)
            for args in [(999, self.member, '2025-01-01', '2025-01-15'), (self.copy, self.member, '2025-02-30', '2025-03-15'), (self.copy, self.member, '2025-01-10', '2025-01-01'), (self.copy, self.member, '20250101', '2025-01-15')]:
                with self.assertRaises(sqlite3.IntegrityError), conn:
                    conn.execute('INSERT INTO loans(copy_id,member_id,borrowed_on,due_on) VALUES (?,?,?,?)', args)
            with conn:
                conn.execute('INSERT INTO loans(copy_id,member_id,borrowed_on,due_on,returned_on) VALUES (?,?,?,?,?)', (self.copy, self.member, '2025-01-01', '2025-01-15', '2025-01-10'))
            with self.assertRaises(sqlite3.IntegrityError), conn:
                conn.execute('INSERT INTO loans(copy_id,member_id,borrowed_on,due_on,returned_on) VALUES (?,?,?,?,?)', (self.copy, self.member, '2025-01-09', '2025-01-23', '2025-01-11'))
            with self.assertRaises(sqlite3.IntegrityError), conn:
                conn.execute("UPDATE loans SET returned_on='2024-12-31'")

    def test_date_parser_future_and_search_safety(self):
        for value in ['2025-02-30', '20250101', '2025-1-1', 'wrong']:
            with self.assertRaises(ValueError):
                iso_day(value)
        with patch('library_lab.service.today', return_value=__import__('datetime').date(2025, 1, 1)):
            with self.assertRaises(ValueError):
                service.borrow(self.copy, self.member, '2025-01-02', self.db)
        self.assertEqual(service.search_books("' OR 1=1 --", self.db), [])
        self.assertEqual(service.search_books('%', self.db), [])
        self.assertEqual(len(service.search_books('Python', self.db)), 1)

    def test_initializer_never_overwrites(self):
        before = self.db.read_bytes()
        with self.assertRaises(ValueError):
            initialize(self.db, sample=True)
        self.assertEqual(self.db.read_bytes(), before)


class SampleTests(unittest.TestCase):
    def test_counts_reproducibility_and_no_overlap(self):
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp)/'a.db', Path(temp)/'b.db'
            initialize(first, sample=True)
            initialize(second, sample=True)
            with connect(first) as a, connect(second) as b:
                for table, count in [('books', 20), ('book_copies', 40), ('members', 30), ('loans', 150)]:
                    rows = [tuple(r) for r in a.execute(f'SELECT * FROM {table} ORDER BY 1')]
                    self.assertEqual(len(rows), count)
                    self.assertEqual(rows, [tuple(r) for r in b.execute(f'SELECT * FROM {table} ORDER BY 1')])
                overlaps = a.execute("""SELECT COUNT(*) FROM loans a JOIN loans b ON a.copy_id=b.copy_id AND a.loan_id<b.loan_id
                WHERE a.borrowed_on <= COALESCE(b.returned_on,'9999-12-31') AND b.borrowed_on <= COALESCE(a.returned_on,'9999-12-31')""").fetchone()[0]
                self.assertEqual(overlaps, 0)
                self.assertEqual(a.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(a.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(len(service.active_loans(first, True, '2025-12-31')), 10)
            self.assertEqual(len(service.active_loans(first, False, '2025-12-31')), 20)
            self.assertEqual(len(service.available_copies(first)), 20)


if __name__ == '__main__':
    unittest.main()
