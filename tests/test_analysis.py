import tempfile
import unittest
from pathlib import Path
from library_lab.init_db import initialize
from library_lab.analyze import analyze, load_tables


class AnalysisTests(unittest.TestCase):
    def test_totals_and_exports(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / 'sample.db'
            initialize(db, sample=True)
            frames = analyze(db, Path(temp)/'results', '2025-12-31')
            for name in ['top_books', 'monthly', 'categories']:
                self.assertEqual(frames[name].loan_count.sum(), 150)
            self.assertEqual(len(frames['returned']), 130)
            self.assertTrue((frames['returned'].duration_days >= 0).all())
            out = Path(temp)/'results'
            self.assertEqual(len(list((out/'figures').glob('*.png'))), 4)
            self.assertEqual(len(list((out/'tables').glob('*.csv'))), 5)
            self.assertIn('10 lượt quá hạn', (out/'report.md').read_text(encoding='utf-8'))

    def test_empty_database(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp)/'empty.db'
            initialize(db)
            self.assertEqual(len(load_tables(db)['loans']), 0)
            analyze(db, Path(temp)/'out', '2025-12-31')
            self.assertEqual(len(list((Path(temp)/'out/figures').glob('*.png'))), 4)


if __name__ == '__main__':
    unittest.main()
