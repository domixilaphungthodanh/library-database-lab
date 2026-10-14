"""Vietnamese terminal menu for the library."""
import argparse
from pathlib import Path
import sqlite3
from . import service
from .db import DEFAULT_DB, connect, iso_day, today

MENU = '''\nQUẢN LÝ THƯ VIỆN
1. Thêm đầu sách
2. Thêm bản sao sách
3. Tìm sách (tên / tác giả / danh mục)
4. Đăng ký độc giả
5. Xem độc giả
6. Mượn sách
7. Trả sách
8. Xem lượt đang mượn
9. Xem bản sao còn sẵn
10. Xem lượt quá hạn
0. Thoát'''


def positive_id(prompt):
    try:
        value = int(input(prompt))
    except ValueError:
        raise ValueError('Mã phải là số nguyên dương.') from None
    if value <= 0:
        raise ValueError('Mã phải là số nguyên dương.')
    return value


def show(rows):
    if not rows:
        print('Không có kết quả.')
    for row in rows:
        print(' | '.join(f'{key}: {value if value is not None else "—"}' for key, value in row.items()))


def main():
    parser = argparse.ArgumentParser(description='Menu quản lý thư viện')
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--as-of', help='Ngày tham chiếu để XEM quá hạn (YYYY-MM-DD)')
    args = parser.parse_args()
    try:
        day = iso_day(args.as_of) if args.as_of else today().isoformat()
        with connect(args.db, readonly=True) as conn:
            conn.execute('SELECT 1 FROM books').fetchone()
    except (ValueError, sqlite3.Error) as exc:
        parser.exit(1, f'Lỗi: {exc}\n')
    print(f'Ngày tham chiếu xem quá hạn: {day}. Ngày mượn/trả mặc định là ngày thực tế UTC+7.')
    while True:
        try:
            print(MENU)
            choice = input('Chọn: ').strip()
            if choice == '0':
                return
            if choice == '1':
                result = service.add_book(input('Tên sách: '), input('Tác giả: '), input('Danh mục: '), db=args.db)
                print(f'Đã thêm đầu sách #{result}.')
            elif choice == '2':
                result = service.add_copy(positive_id('Mã đầu sách: '), input('Mã cuốn duy nhất: '), db=args.db)
                print(f'Đã thêm bản sao #{result}.')
            elif choice == '3':
                show(service.search_books(input('Từ khóa (Enter để xem tất cả): '), db=args.db))
            elif choice == '4':
                result = service.add_member(input('Tên độc giả: '), input('Email (có thể bỏ trống): '), db=args.db)
                print(f'Đã đăng ký độc giả #{result}.')
            elif choice == '5':
                show(service.list_members(db=args.db))
            elif choice == '6':
                result = service.borrow(positive_id('Mã bản sao (copy_id): '), positive_id('Mã độc giả: '), input('Ngày mượn YYYY-MM-DD (Enter = hôm nay): ').strip() or None, db=args.db)
                print(f'Đã tạo lượt mượn #{result}. Hạn trả sau 14 ngày.')
            elif choice == '7':
                service.return_book(positive_id('Mã lượt mượn: '), input('Ngày trả YYYY-MM-DD (Enter = hôm nay): ').strip() or None, db=args.db)
                print('Đã ghi nhận trả sách.')
            elif choice == '8':
                show(service.active_loans(db=args.db, as_of=day))
            elif choice == '9':
                show(service.available_copies(db=args.db))
            elif choice == '10':
                show(service.active_loans(db=args.db, overdue_only=True, as_of=day))
            else:
                print('Lựa chọn không hợp lệ.')
        except EOFError:
            return
        except KeyboardInterrupt:
            print('\nĐã thoát.')
            return
        except (ValueError, sqlite3.Error, OSError) as exc:
            print(f'Lỗi: {exc}')


if __name__ == '__main__':
    main()
