from django.urls import reverse
from parameterized import parameterized
from rest_framework import status
from cases.models import CaseNote
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class CaseNotesGovCreateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.url = reverse("cases:case_notes", kwargs={"pk": self.case.id})
        self.data = {
            "text": "I Am Easy to Find",
        }

    def test_create_case_note_successful(self):
        response = self.client.post(self.url, data=self.data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CaseNote.objects.count(), 1)
        self.assertEqual(CaseNote.objects.get().text, self.data.get("text"))
        self.assertEqual(CaseNote.objects.get().is_visible_to_exporter, False)

    @parameterized.expand(
        [
            [{}],  # Empty data
            [{"text": ""}],  # Empty text field
            [{"text": "🙂"}],  # Less than two character minimum
            [{"text": "🙂" * 2201}],  # More than two thousand, two hundred character maximum
        ]
    )
    def test_create_case_note_failure(self, data):
        response = self.client.post(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CaseNote.objects.count(), 0)

    @parameterized.expand(CaseStatusEnum.terminal_statuses())
    def test_create_case_note_case_terminal_state_success_gov_user(self, terminal_status):
        self.standard_application.status = get_case_status_by_status(terminal_status)
        self.standard_application.save()

        response = self.client.post(self.url, data=self.data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CaseNotesExporterCreateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.url = reverse("cases:case_notes", kwargs={"pk": self.case.id})
        self.data = {"text": "Days of brutalism"}

    def test_create_case_note_successful(self):
        response = self.client.post(self.url, data=self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CaseNote.objects.count(), 1)
        self.assertEqual(CaseNote.objects.get().text, self.data.get("text"))
        self.assertEqual(CaseNote.objects.get().is_visible_to_exporter, True)

    @parameterized.expand(
        [
            [{}],  # Empty data
            [{"text": ""}],  # Empty text field
            [{"text": "🍌"}],  # Less than two character minimum
            [{"text": "🍌" * 2201}],  # More than two thousand, two hundred character maximum
        ]
    )
    def test_create_case_note_failure(self, data):
        response = self.client.post(self.url, data=data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CaseNote.objects.count(), 0)

    @parameterized.expand(CaseStatusEnum.terminal_statuses())
    def test_create_case_note_case_terminal_state_failure_exporter_user(self, terminal_status):
        self.standard_application.status = get_case_status_by_status(terminal_status)
        self.standard_application.save()

        response = self.client.post(self.url, data=self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CaseNotesViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_clc_query("Query", self.organisation)

        self.url = reverse("cases:case_notes", kwargs={"pk": self.case.id})

    def test_view_case_notes_successful(self):
        self.create_case_note(self.case, "Hairpin Turns", self.gov_user)
        self.create_case_note(self.case, "Not in Kansas", self.gov_user)
        self.create_case_note(self.case, "Dust Swirls In Strange Light", self.gov_user)
        self.create_case_note(self.case, "Rylan", self.exporter_user)

        response = self.client.get(self.url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get("case_notes")), 4)

        response = self.client.get(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get("case_notes")), 1)
