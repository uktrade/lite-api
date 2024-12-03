from parameterized import parameterized
from rest_framework.reverse import reverse

from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from test_helpers.clients import DataTestClient

from .factories import (
    ReportSummaryPrefixFactory,
    ReportSummarySubjectFactory,
)


def prefixes_url(name_filter=None):
    query = f"?name={name_filter}" if name_filter else ""
    return reverse("staticdata:report_summaries:prefixes") + query


class ReportSummaryPrefixesWithNoFilterReturnsEverythingTests(DataTestClient):
    def test_get_report_summary_prefixes_OK(self):
        url = prefixes_url()
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
                    "software for equipment for the development of",
                    "software for equipment for the production of",
                    "software for equipment for the use of",
                    "software for technology for equipment for the development of",
                    "software for technology for equipment for the production of",
                    "software for technology for equipment for the use of",
                    "technology for equipment for the development of",
                    "technology for equipment for the production of",
                    "technology for equipment for the use of",
                    "technology for software for equipment for the development of",
                    "technology for software for equipment for the production of",
                    "technology for software for equipment for the use of",
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
        url = prefixes_url(filter)

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        prefixes = [prefix["name"] for prefix in response.json()["report_summary_prefixes"]]
        self.assertEqual(len(prefixes), len(expected_results))
        self.assertEqual(prefixes, expected_results)


def subjects_url(name_filter=None):
    query = f"?name={name_filter}" if name_filter else ""
    return reverse("staticdata:report_summaries:subjects") + query


class ReportSummarySubjectsTests(DataTestClient):
    def test_get_report_summary_subjects_OK(self):
        url = subjects_url()
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        subjects = response.json()["report_summary_subjects"]
        self.assertTrue(len(subjects) > 0)
        self.assertEqual(len(subjects), ReportSummarySubject.objects.count())

        for subject in subjects:
            db_subject = ReportSummarySubject.objects.get(id=(subject["id"]))

            self.assertEqual(subject["id"], str(db_subject.id))
            self.assertEqual(subject["name"], db_subject.name)

    @parameterized.expand(
        [
            [
                "mix of prefix and contains results and sorts with prefixed first",
                "roto",
                [
                    "rotor assembly equipment",
                    "rotor fabrication equipment",
                    "internet protocol network communications surveillance equipment",
                    "technology for helicopter/tilt rotor aircraft power transfer systems",
                ],
            ],
            [
                "single result by narrowing filter",
                "rotoc",
                [
                    "internet protocol network communications surveillance equipment",
                ],
            ],
        ]
    )
    def test_get_report_summary_subjects_with_name_filter(self, name, filter, expected_results):
        url = subjects_url(filter)
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)

        subjects = [subject["name"] for subject in response.json()["report_summary_subjects"]]
        self.assertEqual(len(subjects), len(expected_results))

        self.assertEqual(subjects, expected_results)


class ReportSummarySubjectDetailTests(DataTestClient):
    def test_report_summary_subject_object_not_found(self):
        url = reverse(
            "staticdata:report_summaries:subject",
            kwargs={
                "pk": "fe1059fd-d756-42a6-bd1b-84d83396e3f9",
            },
        )
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 404)

    def test_report_summary_subject_object_found(self):
        report_summary_subject = ReportSummarySubjectFactory.create()
        url = reverse(
            "staticdata:report_summaries:subject",
            kwargs={
                "pk": report_summary_subject.pk,
            },
        )
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "report_summary_subject": {
                    "id": str(report_summary_subject.pk),
                    "name": report_summary_subject.name,
                }
            },
        )


class ReportSummaryPrefixDetailTests(DataTestClient):
    def test_report_summary_prefix_object_not_found(self):
        url = reverse(
            "staticdata:report_summaries:prefix",
            kwargs={
                "pk": "fe1059fd-d756-42a6-bd1b-84d83396e3f9",
            },
        )
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 404)

    def test_report_summary_prefix_object_found(self):
        report_summary_prefix = ReportSummaryPrefixFactory.create()
        url = reverse(
            "staticdata:report_summaries:prefix",
            kwargs={
                "pk": report_summary_prefix.pk,
            },
        )
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "report_summary_prefix": {
                    "id": str(report_summary_prefix.pk),
                    "name": report_summary_prefix.name,
                }
            },
        )
