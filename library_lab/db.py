"""Shared connection and validation helpers."""
from contextlib import contextmanager
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / 'database' / 'library.db'


def today():
    """Calendar date in Vietnam (UTC+7), independent of runner timezone."""
    return datetime.now(timezone(timedelta(hours=7))).date()


def iso_day(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError('Ngày phải hợp lệ và có dạng YYYY-MM-DD.') from None
    if parsed.isoformat() != value:
        raise ValueError('Ngày phải có dạng YYYY-MM-DD.')
    return value


def required(value, label):
    value = value.strip()
    if not value:
        raise ValueError(f'{label} không được để trống.')
    return value


@contextmanager
def connect(db=DEFAULT_DB, readonly=False):
    path = Path(db).resolve()
    if not path.is_file():
        raise ValueError('Database chưa tồn tại. Chạy python -m library_lab.init_db trước.')
    mode = 'ro' if readonly else 'rw'
    conn = sqlite3.connect(f'{path.as_uri()}?mode={mode}', uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        yield conn
    finally:
        conn.close()
