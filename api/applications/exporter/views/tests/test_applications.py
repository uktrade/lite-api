from parameterized import parameterized

from django.urls import reverse
from rest_framework import status

from api.applications.tests.factories import StandardApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.organisations.tests.factories import OrganisationFactory

from test_helpers.clients import DataTestClient


class TestChangeStatus(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory(organisation=self.exporter_user.organisation)
        self.url = reverse(
            "exporter_applications:change_status",
            kwargs={
                "pk": str(self.application.pk),
            },
        )

    @parameterized.expand(
        [
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.WITHDRAWN),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.APPLICANT_EDITING),
            (CaseStatusEnum.INITIAL_CHECKS, CaseStatusEnum.APPLICANT_EDITING),
            (CaseStatusEnum.REOPENED_FOR_CHANGES, CaseStatusEnum.APPLICANT_EDITING),
        ]
    )
    def test_change_status_success(self, original_status, new_status):
        self.application.status = CaseStatus.objects.get(status=original_status)
        self.application.save()
        response = self.client.post(self.url, **self.exporter_headers, data={"status": new_status})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application_id = response.json().get("id")
        self.assertEqual(application_id, str(self.application.id))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, new_status)

    @parameterized.expand(
        [
            (CaseStatusEnum.FINALISED, CaseStatusEnum.WITHDRAWN),
            (CaseStatusEnum.SUBMITTED, CaseStatusEnum.SURRENDERED),
            (CaseStatusEnum.OGD_ADVICE, CaseStatusEnum.APPLICANT_EDITING),
            (CaseStatusEnum.FINALISED, CaseStatusEnum.APPLICANT_EDITING),
        ]
    )
    def test_change_status_status_change_not_permitted(self, original_status, new_status):
        self.application.status = CaseStatus.objects.get(status=original_status)
        self.application.save()
        response = self.client.post(self.url, **self.exporter_headers, data={"status": new_status})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, original_status)

    def test_change_status_application_not_found(self):
        self.application.delete()

        response = self.client.post(
            self.url, **self.exporter_headers, data={"status": CaseStatusEnum.APPLICANT_EDITING}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_status_application_wrong_organisation(self):
        original_status = CaseStatusEnum.INITIAL_CHECKS
        self.application.status = CaseStatus.objects.get(status=original_status)
        self.application.organisation = OrganisationFactory()
        self.application.save()

        response = self.client.post(
            self.url, **self.exporter_headers, data={"status": CaseStatusEnum.APPLICANT_EDITING}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, original_status)
