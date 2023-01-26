import csv
import os

from contextlib import contextmanager

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "report_summaries",
    "migrations",
    "data",
    "0002_add_report_summaries",
)


@contextmanager
def open_csv_file(filename):
    file_path = os.path.join(DATA_PATH, f"{filename}.csv")
    with open(file_path) as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        yield reader


class TestReportSummary:
    def test_report_summary_data(self):
        with open_csv_file("report_summary_prefixes") as reader:
            assert len([i for (i, row) in enumerate(reader)]) == 38

        with open_csv_file("report_summary_subjects") as reader:
            assert len([i for (i, row) in enumerate(reader)]) == 1052
