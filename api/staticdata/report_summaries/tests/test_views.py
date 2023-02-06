from parameterized import parameterized
from rest_framework.reverse import reverse

from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from test_helpers.clients import DataTestClient


def get_url(name_filter=None):
    query = f"?name={name_filter}" if name_filter else ""
    return reverse("staticdata:report_summaries:prefix") + query


class ReportSummaryPrefixesWithNoFilterReturnsEverythingTests(DataTestClient):
    def test_get_report_summary_prefixes_OK(self):
        url = get_url()
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        prefixes = response.json()["report_summary_prefixes"]
        self.assertTrue(len(prefixes) > 0)
        self.assertEqual(len(prefixes), ReportSummaryPrefix.objects.count())

        for prefix in prefixes:
            db_prefix = ReportSummaryPrefix.objects.get(id=(prefix["id"]))

            self.assertEqual(prefix["id"], str(db_prefix.id))
            self.assertEqual(prefix["name"], db_prefix.name)

    @parameterized.expand(
        [
            [
                "mix of prefix and contains results and sorts with prefixed first",
                "eq",
                [
                    "equipment for the development of",
                    "equipment for the production of",
                    "equipment for the use of",
                    "alignment equipment for",
                    "calibration equipment for",
                    "control equipment for",
                    "counter-countermeasure equipment for",
                    "countermeasure equipment for",
                    "decoying equipment for",
                    "fire simulation equipment for",
                    "guidance equipment for",
                    "information security equipment",
                    "launching/handling/control equipment for",
                    "launching/handling/control/support equipment for",
                    "oil and gas industry equipment/materials",
                    "software enabling equipment to function as",
                    "test equipment for",
                    "training equipment for",
                ],
            ],
            [
                "single result by narrowing filter",
                "equipment to",
                [
                    "software enabling equipment to function as",
                ],
            ],
        ]
    )
    def test_get_report_summary_prefixes_with_name_filter(self, name, filter, expected_results):
        url = get_url(filter)
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        prefixes = [prefix["name"] for prefix in response.json()["report_summary_prefixes"]]
        self.assertEqual(len(prefixes), len(expected_results))

        self.assertEqual(prefixes, expected_results)


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
