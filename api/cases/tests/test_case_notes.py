from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.cases.models import CaseNote, CaseNoteMentions
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class CaseNotesGovCreateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
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

    def test_create_case_note_with_mentions_successful(self):

        self.data["is_urgent"] = True
        self.other_user = self.create_gov_user("test@gmail.com", self.team)  # /PS-IGNORE
        self.other_user_2 = self.create_gov_user("test2@gmail.com", self.team)  # /PS-IGNORE

        mentions = [
            {
                "user": str(self.other_user.baseuser_ptr.id),
            },
            {
                "user": str(self.other_user_2.baseuser_ptr.id),
            },
        ]
        self.data["mentions"] = mentions
        response = self.client.post(self.url, data=self.data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CaseNote.objects.count(), 1)
        self.assertEqual(CaseNote.objects.get().text, self.data.get("text"))
        self.assertEqual(CaseNote.objects.get().is_visible_to_exporter, False)
        self.assertEqual(CaseNote.objects.get().is_urgent, True)
        self.assertEqual(CaseNoteMentions.objects.count(), 2)
        self.assertEqual(response.json()["case_note"]["mentions"][0]["user"]["id"], mentions[0]["user"])
        self.assertEqual(response.json()["case_note"]["mentions"][1]["user"]["id"], mentions[1]["user"])

    def test_create_case_note_with_mentions_unsuccessful(self):

        self.data["is_urgent"] = True
        self.other_user = self.create_gov_user("test@gmail.com", self.team)  # /PS-IGNORE
        mentions = [
            {
                "user": 1234,
            }
        ]
        self.data["mentions"] = mentions
        response = self.client.post(self.url, data=self.data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            [{}],  # Empty data
            [{"text": ""}],  # Empty text field
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
        self.standard_application = self.create_draft_standard_application(self.organisation)
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
        self.create_case_note(self.case, "Hairpin Turns", self.gov_user.baseuser_ptr)
        self.create_case_note(self.case, "Not in Kansas", self.gov_user.baseuser_ptr)
        self.create_case_note(self.case, "Dust Swirls In Strange Light", self.gov_user.baseuser_ptr)
        self.create_case_note(self.case, "Rylan", self.exporter_user.baseuser_ptr)

        response = self.client.get(self.url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get("case_notes")), 4)

        response = self.client.get(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get("case_notes")), 1)

    def test_view_case_notes_from_a_draft_application(self):
        case = self.create_draft_standard_application(self.organisation)
        case_note = self.create_case_note(case, "This is cool text", self.exporter_user.baseuser_ptr, True)
        url = reverse("cases:case_notes", kwargs={"pk": case.id})

        response = self.client.get(url, **self.exporter_headers)

        self.assertIn(str(case_note.id), str(response.json()))

    def test_view_pre_submitted_case_notes_post_submit(self):
        case = self.create_draft_standard_application(self.organisation)
        url = reverse("cases:case_notes", kwargs={"pk": case.id})
        text = "Days of brutalism for case note persistence test"
        data = {"text": text}
        response = self.client.post(url, data, **self.exporter_headers)
        case_note_id = response.json().get("case_note").get("id")

        self.submit_application(case)

        url = reverse("cases:case_notes", kwargs={"pk": case.id})
        response = self.client.get(url, **self.gov_headers)

        self.assertIn(case_note_id, str(response.json()))

        response = self.client.get(reverse("cases:activity", kwargs={"pk": case.id}), **self.gov_headers)
        self.assertIn(text, str(response.json()))


class CaseNoteMentionsViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_clc_query("Query", self.organisation)
        self.url = reverse("cases:case_note_mentions", kwargs={"pk": self.case.id})

    def test_view_case_mentions_successful(self):

        case_note = self.create_case_note(self.case, "Hairpin Turns", self.gov_user.baseuser_ptr)
        self.other_user = self.create_gov_user("test@gmail.com", self.team)  # /PS-IGNORE
        self.create_case_note_mention(case_note, self.other_user)
        response = self.client.get(self.url, **self.gov_headers)
        result = response.json()

        self.assertEqual(result["count"], 1)

        self.assertEqual(result["results"][0]["user"]["id"], str(self.other_user.baseuser_ptr.id))
        self.assertEqual(result["results"][0]["case_note_user"]["id"], str(self.gov_user.baseuser_ptr.id))
        self.assertEqual(result["results"][0]["case_note_text"], case_note.text)
        self.assertEqual(result["results"][0]["is_urgent"], case_note.is_urgent)
