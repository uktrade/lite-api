from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from api.applications.enums import ServiceEquipmentType
from cases.enums import CaseTypeEnum
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class ApplicationQuestionsTest(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_mod_clearance_application(
            self.organisation, CaseTypeEnum.F680, additional_information=False
        )
        self.url = reverse("applications:application", kwargs={"pk": self.draft.id})
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_update_f680_questions_success(self):
        data = {"foreign_technology": True, "foreign_technology_description": "This is going to Norway."}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.draft.foreign_technology, data["foreign_technology"])
        self.assertEqual(self.draft.foreign_technology_description, data["foreign_technology_description"])

    def test_update_questions_minor_edit_fail(self):
        self.draft.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        self.draft.save()

        data = {"foreign_technology": True, "foreign_technology_description": "This is going to Norway."}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"Additional details": ["This isn't possible on a minor edit"]}})

    def test_update_f680_questions_bad_data_failure(self):
        data = {"foreign_technology": "FAKE DATA"}

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"foreign_technology": ["Must be a valid boolean."]}})

    def test_update_f680_questions_without_conditional_fail(self):
        data = {
            "expedited": True,
        }

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"expedited_date": ["Enter the date you need the clearance"]}})

    def test_update_f680_questions_with_conditional_success(self):
        date = timezone.now().date()
        data = {
            "expedited": True,
            "expedited_date": f"{date.year}-{str(date.month).zfill(2)}-{str(date.day).zfill(2)}",
        }

        response = self.client.put(self.url, data, **self.exporter_headers)
        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.draft.expedited, data["expedited"])
        self.assertEqual(str(self.draft.expedited_date), data["expedited_date"])

    def test_update_f680_questions_enum_success_type(self):
        data = {
            "uk_service_equipment": True,
            "uk_service_equipment_type": ServiceEquipmentType.MOD_FUNDED,
        }

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
