"""Export four Seaborn charts, CSV summaries and a Markdown report."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from .db import DEFAULT_DB, ROOT, connect, iso_day, today


def load_tables(db=DEFAULT_DB):
    with connect(db, readonly=True) as conn:
        loans = pd.read_sql_query('''SELECT l.*,b.book_id,b.title,b.category
        FROM loans l JOIN book_copies c ON c.copy_id=l.copy_id
        JOIN books b ON b.book_id=c.book_id ORDER BY l.loan_id''', conn)
    loans['borrowed_on'] = pd.to_datetime(loans['borrowed_on'])
    loans['returned_on'] = pd.to_datetime(loans['returned_on'])
    books = loans.groupby(['book_id', 'title'], as_index=False).size().rename(columns={'size': 'loan_count'})
    books = books.sort_values(['loan_count', 'book_id'], ascending=[False, True])
    monthly = loans.assign(month=loans['borrowed_on'].dt.strftime('%Y-%m')).groupby('month', as_index=False).size().rename(columns={'size': 'loan_count'})
    # Include zero-loan months between first and last observed month.
    if not monthly.empty:
        months = pd.period_range(monthly.month.min(), monthly.month.max(), freq='M').astype(str)
        monthly = monthly.set_index('month').reindex(months, fill_value=0).rename_axis('month').reset_index()
    categories = loans.groupby('category', as_index=False).size().rename(columns={'size': 'loan_count'})
    returned = loans.loc[loans.returned_on.notna(), ['loan_id', 'borrowed_on', 'returned_on']].copy()
    returned['duration_days'] = (returned.returned_on - returned.borrowed_on).dt.days
    assert len(loans) == books.loan_count.sum() == monthly.loan_count.sum() == categories.loan_count.sum()
    return {'loans': loans, 'top_books': books, 'monthly': monthly, 'categories': categories, 'returned': returned}


def analyze(db=DEFAULT_DB, output=None, as_of=None):
    out = Path(output) if output else ROOT / 'outputs'
    out = out.resolve()
    day = iso_day(as_of if as_of is not None else today())
    tables = load_tables(db)
    for folder in ['tables', 'figures']:
        (out / folder).mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(out / 'tables' / f'{name}.csv', index=False)
    sns.set_theme(style='whitegrid', font='DejaVu Sans')
    configs = [
        ('01_top_books', tables['top_books'].head(10), 'title', 'Top 10 đầu sách theo lượt mượn'),
        ('02_monthly_loans', tables['monthly'], 'month', 'Lượt mượn theo tháng'),
        ('03_category_loans', tables['categories'], 'category', 'Lượt mượn theo danh mục'),
        ('04_loan_duration', tables['returned'], 'duration_days', 'Thời gian mượn của lượt đã trả'),
    ]
    for name, frame, column, title in configs:
        fig, ax = plt.subplots(figsize=(10, 5))
        if frame.empty:
            ax.text(.5, .5, 'Chưa có dữ liệu phù hợp', ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
        elif column == 'title':
            sns.barplot(data=frame, x='loan_count', y=column, color='#3282b8', ax=ax)
            ax.set(xlabel='Số lượt mượn', ylabel='Đầu sách')
        elif column == 'month':
            sns.lineplot(data=frame, x=column, y='loan_count', marker='o', ax=ax)
            ax.set(xlabel='Tháng', ylabel='Số lượt mượn')
            ax.tick_params(axis='x', rotation=45)
        elif column == 'category':
            sns.barplot(data=frame, x=column, y='loan_count', color='#3282b8', ax=ax)
            ax.set(xlabel='Danh mục', ylabel='Số lượt mượn')
        else:
            sns.histplot(data=frame, x=column, discrete=True, ax=ax)
            ax.set(xlabel='Số ngày mượn', ylabel='Số lượt đã trả')
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(out / 'figures' / f'{name}.png', dpi=160)
        plt.close(fig)
    loans = tables['loans']
    active = loans.loc[loans.returned_on.isna()]
    overdue = int((active.due_on < day).sum())
    summary = [
        '# Báo cáo thư viện\n',
        f'Ngày tham chiếu: {day}. Tổng lượt mượn: {len(loans)}. Lượt đang mượn: {len(active)}. Lượt đang quá hạn: {overdue}.\n',
        '## Ba nhận xét\n',
    ]
    if not loans.empty:
        top = tables['top_books'].iloc[0]
        peak = tables['monthly'].sort_values(['loan_count', 'month'], ascending=[False, True]).iloc[0]
        summary += [
            f"1. Một đầu sách dẫn đầu là **{top.title}**, có **{int(top.loan_count)} lượt mượn**; các đầu sách có thể đồng hạng.",
            f"2. Một tháng có nhiều lượt mượn nhất là **{peak.month}**, có **{int(peak.loan_count)} lượt**.",
            f"3. Trong **{len(active)} lượt đang mượn**, có **{overdue} lượt quá hạn** tại ngày tham chiếu.",
        ]
    else:
        summary += ['1. Chưa có lượt mượn.', '2. Chưa thể xếp hạng đầu sách hoặc tháng.', '3. Chưa thể đánh giá quá hạn.']
    summary += [
        '\n## Giới hạn\n',
        'Dữ liệu do --sample tạo là GIẢ LẬP (seed 42), không phản ánh nhu cầu đọc thực tế. Nếu đã nhập dữ liệu thật, hãy cập nhật mô tả nguồn dữ liệu trước khi chia sẻ báo cáo.',
        'Dữ liệu mẫu có ngày tham chiếu 2025-12-31. Ngày này phân loại quá hạn trên dữ liệu mẫu tĩnh; --as-of không tái dựng đầy đủ lịch sử trạng thái tại một thời điểm quá khứ.',
        'Lượt mượn không phải số độc giả duy nhất; thống kê thời gian mượn chỉ dùng lượt đã trả, nên có thể bỏ sót các lượt đang kéo dài. Chưa chuẩn hóa mức độ phổ biến theo số bản sao hoặc thời gian có sẵn.',
        'Không kết luận quan hệ nhân quả hoặc mùa vụ chỉ từ các biểu đồ này.',
    ]
    (out / 'report.md').write_text('\n\n'.join(summary) + '\n', encoding='utf-8')
    print(f'Đã xuất 4 biểu đồ, 5 bảng CSV và báo cáo tại {out}')
    return tables


def main():
    parser = argparse.ArgumentParser(description='Phân tích dữ liệu thư viện bằng Seaborn')
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--as-of', help='Ngày tham chiếu quá hạn; mặc định hôm nay UTC+7')
    args = parser.parse_args()
    try:
        analyze(args.db, args.output, args.as_of)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Lỗi: {exc}\n')


if __name__ == '__main__':
    main()
