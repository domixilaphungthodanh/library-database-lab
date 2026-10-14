"""Create a NEW SQLite database; existing paths are never overwritten."""
import argparse
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from .db import DEFAULT_DB, ROOT

SAMPLE_AS_OF = date(2025, 12, 31)


def sample_rows(conn):
    rng = random.Random(42)
    categories = ['Khoa học', 'Văn học', 'Lịch sử', 'Công nghệ']
    for i in range(1, 21):
        conn.execute('INSERT INTO books VALUES (?,?,?,?)', (i, f'Sách mẫu {i:02d}', f'Tác giả {(i-1)//2+1:02d}', categories[(i-1) % 4]))
    for i in range(1, 41):
        conn.execute('INSERT INTO book_copies VALUES (?,?,?)', (i, (i-1)//2+1, f'COPY-{i:03d}'))
    for i in range(1, 31):
        conn.execute('INSERT INTO members VALUES (?,?,?)', (i, f'Độc giả {i:02d}', f'reader{i:02d}@example.com'))
    # 130 completed loans, sequenced independently on each physical copy.
    next_day = {i: date(2025, 1, 1) + timedelta(days=rng.randrange(30)) for i in range(1, 41)}
    for i in range(130):
        copy_id = i % 40 + 1
        start = next_day[copy_id]
        end = start + timedelta(days=rng.randint(2, 24))
        conn.execute('INSERT INTO loans(copy_id,member_id,borrowed_on,due_on,returned_on) VALUES (?,?,?,?,?)',
                     (copy_id, rng.randint(1, 30), start.isoformat(), (start+timedelta(days=14)).isoformat(), end.isoformat()))
        next_day[copy_id] = end + timedelta(days=rng.randint(2, 15))
    # 20 open loans: 10 overdue and 10 not overdue at the fixed reference date.
    for i in range(1, 21):
        start = SAMPLE_AS_OF - timedelta(days=20 if i <= 10 else 5)
        conn.execute('INSERT INTO loans(copy_id,member_id,borrowed_on,due_on) VALUES (?,?,?,?)',
                     (i, rng.randint(1, 30), start.isoformat(), (start+timedelta(days=14)).isoformat()))


def initialize(db=DEFAULT_DB, sample=False):
    path = Path(db).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Exclusive creation also protects against races between two initializers.
        with path.open('xb'):
            pass
    except FileExistsError:
        raise ValueError(f'Database đã tồn tại: {path}. Dùng --db với đường dẫn khác.') from None
    conn = None
    try:
        conn = sqlite3.connect(path)
        conn.execute('PRAGMA foreign_keys = ON')
        conn.executescript((ROOT / 'sql/schema.sql').read_text(encoding='utf-8'))
        with conn:
            if sample:
                sample_rows(conn)
            if conn.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Dữ liệu mẫu có lỗi khóa ngoại.')
    except Exception:
        if conn is not None:
            conn.close()
            conn = None
        path.unlink(missing_ok=True)  # Only the new file created by this call.
        raise
    finally:
        if conn is not None:
            conn.close()
    return path


def main():
    parser = argparse.ArgumentParser(description='Tạo database mới; không ghi đè dữ liệu.')
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--sample', action='store_true', help='Tạo dữ liệu giả lập seed 42')
    args = parser.parse_args()
    try:
        path = initialize(args.db, args.sample)
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f'Lỗi: {exc}\n')
    print(f'Đã tạo: {path}')
    if args.sample:
        print('Dữ liệu GIẢ LẬP: 20 đầu sách, 40 bản sao, 30 độc giả, 150 lượt mượn.')
        print('Ngày tham chiếu mẫu: 2025-12-31. Phân tích quá hạn mẫu dùng ngày này.')


if __name__ == '__main__':
    main()
