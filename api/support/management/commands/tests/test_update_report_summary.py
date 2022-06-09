from django.core.management import call_command
from tempfile import NamedTemporaryFile

from test_helpers.clients import DataTestClient


class UpdateReportSummaryMgmtCommandTests(DataTestClient):
    def test_update_report_summary_command(self):
        self.application = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.application)
        self.assertIsNone(self.application.goods.all()[0].report_summary)

        with NamedTemporaryFile(suffix=".csv", delete=True) as tmp_file:
            rows = [
                "case_reference,line_item,updated_report_summary",
                f"{self.application.reference_code},1,updated report summary1",
                f"{self.application.reference_code},1,updated report summary2",
            ]
            tmp_file.write("\n".join(rows).encode("utf-8"))
            tmp_file.flush()

            call_command("update_report_summary", tmp_file.name)
            self.application.refresh_from_db()
            self.assertEqual(self.application.goods.all()[0].report_summary, "updated report summary2")

    def test_update_report_summary_command_invalid_line_item(self):
        self.application = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.application)
        self.assertIsNone(self.application.goods.all()[0].report_summary)

        with NamedTemporaryFile(suffix=".csv", delete=True) as tmp_file:
            rows = [
                "case_reference,line_item,updated_report_summary",
                f"{self.application.reference_code},2,updated report summary",
            ]
            tmp_file.write("\n".join(rows).encode("utf-8"))
            tmp_file.flush()

            call_command("update_report_summary", tmp_file.name)
            self.application.refresh_from_db()
            self.assertIsNone(self.application.goods.all()[0].report_summary)

        with NamedTemporaryFile(suffix=".csv", delete=True) as tmp_file:
            rows = [
                "case_reference,line_item,updated_report_summary",
                f"{self.application.reference_code},-1,updated report summary",
            ]
            tmp_file.write("\n".join(rows).encode("utf-8"))
            tmp_file.flush()

            call_command("update_report_summary", tmp_file.name)
            self.application.refresh_from_db()
            self.assertIsNone(self.application.goods.all()[0].report_summary)
