import uuid

from django.urls import reverse
from rest_framework import status

from cases.enums import CaseTypeEnum
from test_helpers.clients import DataTestClient


class ApplicationQuestionsTest(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        self.url = reverse("applications:application_questions", kwargs={"pk": self.draft.id})
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
    #
    # def test_update_f680_questions(self):
    #     self.assertIsNone(self.draft.questions)
    #
    #     data = {"foreign_technology": True, "foreign_technology_description": "This is going to Norway."}
    #
    #     response = self.client.post(self.url, data, **self.exporter_headers)
    #     self.draft.refresh_from_db()
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(self.draft.questions, data)
    #
    # def test_update_f680_questions_failure(self):
    #     self.assertIsNone(self.draft.questions)
    #
    #     data = {"foreign_technology": ['Must be a valid boolean.']}
    #
    #     response = self.client.post(self.url, data, **self.exporter_headers)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.json(), {"errors": data})
    #
    # def test_update_f680_questions_2(self):
    #     self.assertIsNone(self.draft.questions)
    #
    #     data = {
    #         "electronic_warfare_requirement": False,
    #     }
    #
    #     response = self.client.post(self.url, data, **self.exporter_headers)
    #
    #     self.draft.refresh_from_db()
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(self.draft.questions, data)
    #
    # def test_update_f680_questions_failure(self):
    #     self.assertIsNone(self.draft.questions)
    #
    #     data = {
    #         "electronic_warfare_requirement": True,
    #     }
    #
    #     response = self.client.post(self.url, data, **self.exporter_headers)
    #
    #     self.draft.refresh_from_db()
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.json(), {"errors": {'electronic_warfare_requirement_attachment': ['Attachment required.']}})
    #     self.assertIsNone(self.draft.questions)
    #
    # def test_update_f680_questions_failure_2(self):
    #     self.assertIsNone(self.draft.questions)
    #
    #     data = {
    #         "electronic_warfare_requirement": True,
    #         "electronic_warfare_attachment": "HELLO",
    #     }
    #
    #     response = self.client.post(self.url, data, **self.exporter_headers)
    #
    #     self.draft.refresh_from_db()
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.json(), {'errors': {'electronic_warfare_requirement_attachment': ['Attachment required.']}})
    #     self.assertIsNone(self.draft.questions)
    #
    # def test_update_f680_questions_success_2(self):
    #     self.assertIsNone(self.draft.questions)
    #
    #     data = {
    #         "electronic_warfare_requirement": True,
    #         "electronic_warfare_requirement_attachment": str(uuid.uuid4()),
    #     }
    #
    #     response = self.client.post(self.url, data, **self.exporter_headers)
    #
    #     self.draft.refresh_from_db()
    #     print(response.json())
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(self.draft.questions, data)
    #

    def test_update_f680_questions_success_3(self):
        self.assertIsNone(self.draft.questions)

        data = {
            "expedited": True,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'errors': {'expedited_date': ['Date required.']}})

    def test_update_f680_questions_success_3(self):
        self.assertIsNone(self.draft.questions)

        data = {
            "expedited": True,
            "expedited": "GEL",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'errors': {'expedited_date': ['Date required.']}})
