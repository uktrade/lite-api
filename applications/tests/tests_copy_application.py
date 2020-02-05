from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy

from applications.enums import (
    ApplicationType,
    ApplicationExportType,
    ApplicationExportLicenceOfficialType,
)
from applications.models import (
    StandardApplication,
    OpenApplication,
    HmrcQuery,
    BaseApplication,
    ExhibitionClearanceApplication,
)
from lite_content.lite_api import strings
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class DraftCopyTests(DataTestClient):

    # standard application
    def test_copy_draft_standard_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        original_application = self.create_standard_application(self.organisation)

        url = reverse_lazy("applications:copy", kwargs={"pk": original_application.id})

        data = {"name": "New application", "have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, original_application.id)

        copied_application = StandardApplication.objects.get(id=response_data)

        # check reset data
        self.assertEqual(copied_application.status, get_case_status_by_status(CaseStatusEnum.DRAFT))
        self.assertGreater(copied_application.created_at, original_application.created_at)

        # Check many to many
        new_goods = copied_application.goods.all()
        original_goods = original_application.goods.all()
        for good in new_goods:
            self.assertNotIn(good, original_goods)

        self.assertIsNotNone(copied_application.end_user)
        self.assertNotEqual(original_application.end_user, copied_application.end_user)
        self.assertIsNotNone(copied_application.consignee)
        self.assertNotEqual(original_application.consignee, copied_application.consignee)

        self.assertIsNotNone(copied_application.ultimate_end_users)
        self.assertIsNotNone(copied_application.third_parties)

    def test_copy_submitted_standard_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        original_application = self.create_standard_application_case(self.organisation)

        url = reverse_lazy("applications:copy", kwargs={"pk": original_application.id})

        data = {"name": "New application", "have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, original_application.id)

        copied_application = StandardApplication.objects.get(id=response_data)

        # check reset data
        self.assertEqual(copied_application.status, get_case_status_by_status(CaseStatusEnum.DRAFT))
        self.assertGreater(copied_application.created_at, original_application.created_at)

        # Check many to many
        new_goods = copied_application.goods.all()
        original_goods = original_application.goods.all()
        for good in new_goods:
            self.assertNotIn(good, original_goods)

        self.assertIsNotNone(copied_application.end_user)
        self.assertNotEqual(original_application.end_user, copied_application.end_user)
        self.assertIsNotNone(copied_application.consignee)
        self.assertNotEqual(original_application.consignee, copied_application.consignee)

        self.assertIsNotNone(copied_application.ultimate_end_users)
        self.assertIsNotNone(copied_application.third_parties)

        self.assertIsNone(copied_application.reference_code)
        self.assertIsNone(copied_application.case_officer)
        self.assertIsNone(copied_application.submitted_at)
        self.assertIsNone(copied_application.licence_duration)

    def test_copy_draft_open_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        application = self.create_open_application(self.organisation)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application"}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)

    def test_copy_submitted_open_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        application = self.create_open_application(self.organisation)
        self.submit_application(application)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application"}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)

    def test_copy_draft_exhibition_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        application = self.create_exhibition_clearance_application(self.organisation)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application"}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)

    def test_copy_submitted_exhibition_application_successful(self):
        """
        Ensure we can create a new standard application draft object
        """
        application = self.create_exhibition_clearance_application(self.organisation)
        self.submit_application(application)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application"}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)
