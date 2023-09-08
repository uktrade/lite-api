import uuid

from django.urls import reverse

from rest_framework import status

from test_helpers.clients import DataTestClient

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.statuses.models import CaseSubStatus


class ApplicationManageStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.url = reverse("applications:manage_sub_status", kwargs={"pk": self.standard_application.id})

    def test_gov_set_application_sub_status(self):
        self.assertIsNone(self.standard_application.sub_status)

        sub_status = CaseSubStatus.objects.create(
            name="test_sub_status",
            parent_status=self.standard_application.status,
        )

        data = {"sub_status": str(sub_status.pk)}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.standard_application.sub_status,
            sub_status,
        )

    def test_exporter_set_application_sub_status(self):
        self.assertIsNone(self.standard_application.sub_status)

        sub_status = CaseSubStatus.objects.create(
            name="test_sub_status",
            parent_status=self.standard_application.status,
        )

        data = {"sub_status": str(sub_status.pk)}
        response = self.client.put(self.url, data=data, **self.exporter_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(self.standard_application.sub_status)

    def test_set_invalid_sub_status_pk(self):
        self.assertIsNone(self.standard_application.sub_status)

        data = {"sub_status": str(uuid.uuid4())}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(self.standard_application.sub_status)

    def test_set_sub_status_of_different_parent_status(self):
        self.assertIsNone(self.standard_application.sub_status)

        CaseSubStatus.objects.create(
            name="test_sub_status",
            parent_status=self.standard_application.status,
        )
        other_sub_status = CaseSubStatus.objects.create(
            name="other_test_sub_status", parent_status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )

        data = {"sub_status": str(other_sub_status.pk)}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(self.standard_application.sub_status)

    def test_set_sub_status_being_set_to_none(self):
        self.assertIsNone(self.standard_application.sub_status)

        sub_status = CaseSubStatus.objects.create(
            name="test_sub_status",
            parent_status=self.standard_application.status,
        )
        self.standard_application.sub_status = sub_status
        self.standard_application.save()

        data = {"sub_status": None}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(self.standard_application.sub_status)
