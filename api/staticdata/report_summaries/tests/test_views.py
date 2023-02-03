from rest_framework.reverse import reverse

from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from test_helpers.clients import DataTestClient


class ReportSummaryPrefixesTests(DataTestClient):
    def test_get_report_summary_prefixes_OK(self):
        url = reverse("staticdata:report_summaries:prefix")
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        prefixes = response.json()["report_summary_prefixes"]
        self.assertTrue(len(prefixes) > 0)
        self.assertEqual(len(prefixes), ReportSummaryPrefix.objects.count())

        for prefix in prefixes:
            db_prefix = ReportSummaryPrefix.objects.get(id=(prefix["id"]))

            self.assertEqual(prefix["id"], str(db_prefix.id))
            self.assertEqual(prefix["name"], db_prefix.name)


class ReportSummarySubjectsTests(DataTestClient):
    def test_get_report_summary_subjects_OK(self):
        url = reverse("staticdata:report_summaries:subject")
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        subjects = response.json()["report_summary_subjects"]
        self.assertTrue(len(subjects) > 0)
        self.assertEqual(len(subjects), ReportSummarySubject.objects.count())

        for subject in subjects:
            db_subject = ReportSummarySubject.objects.get(id=(subject["id"]))

            self.assertEqual(subject["id"], str(db_subject.id))
            self.assertEqual(subject["name"], db_subject.name)
