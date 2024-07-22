from parameterized import parameterized
from unittest import mock

from django.urls import reverse
from rest_framework import status

from api.applications import models as application_models
from api.applications.models import StandardApplication
from api.applications.tests.factories import StandardApplicationFactory, GoodOnApplicationFactory
from api.licences.tests.factories import StandardLicenceFactory
from api.licences.enums import LicenceStatus
from api.organisations.tests.factories import OrganisationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus

from test_helpers.clients import DataTestClient


class TestCreateApplicationAmendment(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory(organisation=self.organisation)
        self.good_on_application = GoodOnApplicationFactory(application=self.application)
        self.url = reverse(
            "applications:create_amendment",
            kwargs={
                "pk": str(self.application.pk),
            },
        )

    @parameterized.expand(CaseStatusEnum.can_invoke_major_edit_statuses)
    def test_create_amendment(self, case_status):
        self.application.status = CaseStatus.objects.get(status=case_status)
        self.application.save()
        response = self.client.post(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        amendment_id = response.json().get("id")
        amendment_application = StandardApplication.objects.get(id=amendment_id)
        self.assertEqual(amendment_application.name, self.application.name)
        self.assertEqual(amendment_application.amendment_of_id, self.application.id)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, CaseStatusEnum.SUPERSEDED_BY_EXPORTER_EDIT)

    @mock.patch.object(application_models.GoodOnApplication, "clone")
    def test_create_amendment_partial_failure(self, mocked_good_on_application_clone):
        self.assertEqual(list(StandardApplication.objects.all()), [self.application])
        mocked_good_on_application_clone.side_effect = Exception
        with self.assertRaises(Exception):
            response = self.client.post(self.url, **self.exporter_headers)
        self.assertEqual(list(StandardApplication.objects.all()), [self.application])

    def test_create_amendment_exporter_wrong_organisation(self):
        self.application.organisation = OrganisationFactory()
        self.application.save()
        response = self.client.post(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_amendment_application_does_not_exist(self):
        self.application.delete()
        response = self.client.post(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @parameterized.expand(CaseStatusEnum.can_not_invoke_major_edit_statuses)
    def test_create_amendment_application_wrong_status(self, case_status):
        self.application.status = CaseStatus.objects.get(status=case_status)
        self.application.save()
        response = self.client.post(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_amendment_licence_exists_on_original(self):
        licence = StandardLicenceFactory(case=self.application.case_ptr, status=LicenceStatus.ISSUED)
        response = self.client.post(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["non_field_errors"], "Application has at least one licence so cannot be amended."
        )
