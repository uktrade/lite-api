from django.urls import reverse
from api.audit_trail.enums import AuditType
from parameterized import parameterized
from rest_framework import status

from api.cases.models import CaseNote, CaseNoteMentions
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from api.audit_trail.models import Audit


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

        # Check the Audit log
        audit = Audit.objects.get(verb=AuditType.CREATED_CASE_NOTE_WITH_MENTIONS.value)
        self.assertEqual(audit.verb, AuditType.CREATED_CASE_NOTE_WITH_MENTIONS.value)
        mention_users_text = f"{self.other_user.baseuser_ptr.first_name} {self.other_user.baseuser_ptr.last_name}, {self.other_user_2.baseuser_ptr.first_name} {self.other_user_2.baseuser_ptr.last_name} URGENT"
        self.assertEqual(audit.payload["mention_users"], mention_users_text)

    def test_create_case_note_with_mentions_email_audit_check(self):

        self.other_user = self.create_gov_user("test@gmail.com", self.team)  # /PS-IGNORE
        self.other_user.baseuser_ptr.first_name = ""
        self.other_user.baseuser_ptr.save()
        mentions = [
            {
                "user": str(self.other_user.baseuser_ptr.id),
            },
        ]
        self.data["mentions"] = mentions
        self.client.post(self.url, data=self.data, **self.gov_headers)

        # Check the Audit log
        audit = Audit.objects.get(verb=AuditType.CREATED_CASE_NOTE_WITH_MENTIONS.value)
        self.assertEqual(audit.verb, AuditType.CREATED_CASE_NOTE_WITH_MENTIONS.value)
        self.assertEqual(audit.payload["mention_users"], "test@gmail.com")  # /PS-IGNORE

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
        self.url = reverse("cases:case_note_mentions_list", kwargs={"pk": self.case.id})

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


class UserCaseNoteMentionsViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_clc_query("Query", self.organisation)
        self.case_note = self.create_case_note(self.case, "Hairpin Turns", self.gov_user.baseuser_ptr)

        self.other_user = self.create_gov_user("test@gmail.com", self.team)  # /PS-IGNORE
        self.case_other = self.create_clc_query("Query", self.organisation)
        self.case_note_other = self.create_case_note(self.case_other, "Hairpin Turns", self.other_user.baseuser_ptr)

        self.url = reverse("cases:user_case_note_mentions")

    def test_view_user_case_mentions_successful(self):

        self.create_case_note_mention(self.case_note, self.gov_user)
        self.create_case_note_mention(self.case_note, self.other_user)
        self.create_case_note_mention(self.case_note_other, self.gov_user)

        response = self.client.get(self.url, **self.gov_headers)

        result = response.json()["mentions"]
        first_mention = result[0]

        self.assertEqual(len(result), 2)
        self.assertEqual(first_mention["user"]["id"], str(self.gov_user.baseuser_ptr.id))
        self.assertEqual(first_mention["case_note_user"]["id"], str(self.other_user.baseuser_ptr.id))
        self.assertEqual(first_mention["case_note_text"], self.case_note_other.text)
        self.assertEqual(first_mention["case_note"], str(self.case_note_other.id))
        self.assertEqual(first_mention["reference_code"], self.case_note_other.case.reference_code)
        self.assertEqual(first_mention["case_id"], str(self.case_note_other.case.id))
        self.assertEqual(first_mention["is_urgent"], self.case_note_other.is_urgent)
        self.assertEqual(first_mention["is_accessed"], False)
        self.assertEqual(first_mention["team"], None)
        self.assertEqual(first_mention["case_queue_id"], "00000000-0000-0000-0000-000000000001")

    def test_view_user_case_mentions_case_queue_unmatched(self):

        self.case.queues.add(self.create_queue("Test", self.create_team("test")))
        self.case.save()

        self.create_case_note_mention(self.case_note, self.gov_user)

        response = self.client.get(self.url, **self.gov_headers)

        result = response.json()["mentions"]
        first_mention = result[0]

        self.assertEqual(first_mention["case_queue_id"], "00000000-0000-0000-0000-000000000001")

    def test_view_user_case_mentions_case_queue_match(self):

        self.case.queues.add(self.queue)
        self.case.save()

        self.gov_user.team.queue_set.add(self.queue)
        self.gov_user.save()

        self.create_case_note_mention(self.case_note, self.gov_user)

        response = self.client.get(self.url, **self.gov_headers)

        result = response.json()["mentions"]
        first_mention = result[0]

        self.assertEqual(first_mention["case_queue_id"], str(self.queue.id))

    def test_view_user_case_mentions_update(self):

        case_note_mention = self.create_case_note_mention(self.case_note, self.gov_user)
        case_note_mention_2 = self.create_case_note_mention(self.case_note, self.gov_user)
        case_note_mention_2.is_accessed = True
        case_note_mention_2.save()

        self.assertEqual(case_note_mention.is_accessed, False)
        self.assertEqual(case_note_mention_2.is_accessed, True)

        url = reverse("cases:case_note_mentions")
        update_data = [
            {"id": case_note_mention.pk, "is_accessed": True},
            {"id": case_note_mention_2.pk, "is_accessed": False},
        ]

        response = self.client.put(url, data=update_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        case_note_mention.refresh_from_db()
        case_note_mention_2.refresh_from_db()

        self.assertEqual(case_note_mention.is_accessed, True)
        self.assertEqual(case_note_mention_2.is_accessed, False)

    def test_view_user_case_mentions_update_bad_data(self):
        url = reverse("cases:case_note_mentions")
        case_note_mention = self.create_case_note_mention(self.case_note, self.gov_user)

        update_data = [{"id": case_note_mention.pk, "is_accessed": "bad_data"}]

        response = self.client.put(url, data=update_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
