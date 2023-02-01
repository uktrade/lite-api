from rest_framework.reverse import reverse

from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from test_helpers.clients import DataTestClient


class ReportSummaryPrefixesTests(DataTestClient):
    def test_get_report_summary_prefixes_OK(self):
        url = reverse("staticdata:report_summaries:prefix")
        response = self.client.get(url, **self.exporter_headers)
        prefixes = response.json()["report_summary_prefixes"]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(prefixes) > 0)
        self.assertEqual(len(prefixes), ReportSummaryPrefix.objects.count())
        self.assertEqual(prefixes[0]["name"], ReportSummaryPrefix.objects.get(id=(prefixes[0]["id"])).name)


class ReportSummarySubjectsTests(DataTestClient):
    def test_get_report_summary_subjects_OK(self):
        url = reverse("staticdata:report_summaries:subject")
        response = self.client.get(url, **self.exporter_headers)
        subjects = response.json()["report_summary_subjects"]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(subjects) > 0)
        self.assertEqual(len(subjects), ReportSummarySubject.objects.count())
        self.assertEqual(subjects[0]["name"], ReportSummarySubject.objects.get(id=(subjects[0]["id"])).name)
