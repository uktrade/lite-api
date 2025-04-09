import pytest
from parameterized import parameterized

from django.urls import reverse
from rest_framework import status

from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from api.applications.tests.factories import StandardApplicationFactory, ApplicationDocumentFactory
from api.f680.tests.factories import F680ApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus

from test_helpers.clients import DataTestClient

pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


class TestChangeStatus(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory(organisation=self.organisation)
        self.url = reverse(
            "caseworker_applications:change_status",
            kwargs={
                "pk": str(self.application.pk),
            },
        )

    @parameterized.expand(
        list(set(CaseStatusEnum.caseworker_operable_statuses()) - set(CaseStatusEnum.terminal_statuses()))
    )
    def test_change_status_success(self, case_status):
        self.application.status = CaseStatus.objects.get(status=case_status)
        self.application.save()
        response = self.client.post(self.url, **self.gov_headers, data={"status": CaseStatusEnum.SUBMITTED})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application_id = response.json().get("id")
        self.assertEqual(application_id, str(self.application.id))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, CaseStatusEnum.SUBMITTED)

    def test_change_status_success_with_note(self):
        self.application.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        self.application.save()
        response = self.client.post(
            self.url, **self.gov_headers, data={"status": CaseStatusEnum.INITIAL_CHECKS, "note": "some reason"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application_id = response.json().get("id")
        self.assertEqual(application_id, str(self.application.id))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, CaseStatusEnum.INITIAL_CHECKS)
        audit_entry = Audit.objects.get(verb=AuditType.UPDATED_STATUS)
        assert audit_entry.payload == {
            "additional_text": "some reason",
            "status": {
                "new": CaseStatusEnum.INITIAL_CHECKS,
                "old": CaseStatusEnum.SUBMITTED,
            },
        }

    def test_change_status_not_permitted_status(self):
        self.application.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        self.application.save()
        response = self.client.post(self.url, **self.gov_headers, data={"status": CaseStatusEnum.APPLICANT_EDITING})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, CaseStatusEnum.SUBMITTED)

    def test_change_status_not_caseworker_operable(self):
        self.application.status = CaseStatus.objects.get(status=CaseStatusEnum.SUPERSEDED_BY_EXPORTER_EDIT)
        self.application.save()
        response = self.client.post(self.url, **self.gov_headers, data={"status": CaseStatusEnum.OGD_ADVICE})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status.status, CaseStatusEnum.SUPERSEDED_BY_EXPORTER_EDIT)

    def test_change_status_application_not_found(self):
        self.application.delete()
        response = self.client.post(self.url, **self.gov_headers, data={"status": CaseStatusEnum.APPLICANT_EDITING})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_status_exporter_not_permitted(self):
        self.application.organisation = self.exporter_user.organisation
        self.application.save()

        response = self.client.post(self.url, **self.exporter_headers, data={"status": CaseStatusEnum.SUBMITTED})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestApplicationDocuments:

    @pytest.mark.parametrize("application_factory", [StandardApplicationFactory, F680ApplicationFactory])
    def test_GET_success(self, application_factory, api_client, gov_headers, organisation):

        my_application = application_factory(organisation=organisation)
        my_doc_1 = ApplicationDocumentFactory(application=my_application)
        my_doc_2 = ApplicationDocumentFactory(application=my_application)
        other_doc = ApplicationDocumentFactory()

        url = reverse(
            "caseworker_applications:document",
            kwargs={
                "pk": str(my_application.pk),
            },
        )
        response = api_client.get(url, **gov_headers)

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()

        assert response_json["count"] == 2

        result_doc_ids = [r["id"] for r in response_json["results"]]
        result_doc_applications = [r["application"] for r in response_json["results"]]

        assert [str(my_doc_1.id), str(my_doc_2.id)] == result_doc_ids
        assert str(my_application.id) in result_doc_applications
        assert str(other_doc.id) not in result_doc_ids
