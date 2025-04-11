import pytest
import uuid
from django.utils import timezone
from freezegun import freeze_time

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.tests.factories import EcjuQueryFactory
from parameterized import parameterized

from django.urls import reverse
from rest_framework import status

from api.applications.tests.factories import ApplicationDocumentFactory, StandardApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.cases.models import Case, Queue
from api.organisations.tests.factories import OrganisationFactory

from test_helpers.clients import DataTestClient

from api.f680.tests.factories import F680ApplicationFactory  # /PS-IGNORE

pytestmark = pytest.mark.django_db

pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


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


class TestApplicationHistory(DataTestClient):

    @freeze_time("2025-01-01 12:00:01")
    def setUp(self):
        super().setUp()

        self.amendment_1 = StandardApplicationFactory(
            organisation=self.exporter_user.organisation,
            status=CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED),
            submitted_at=timezone.now(),
        )
        self.amendment_1.queues.add(Queue.objects.first())
        self.amendment_1.save()
        EcjuQueryFactory(
            question="ECJU Query 1", case=self.amendment_1, raised_by_user=self.gov_user, responded_at=timezone.now()
        )
        EcjuQueryFactory(question="ECJU Query 2", case=self.amendment_1, raised_by_user=self.gov_user, response=None)

        self.amendment_2 = self.amendment_1.create_amendment(self.exporter_user)
        self.amendment_1.refresh_from_db()
        self.amendment_2.submitted_at = timezone.now()
        self.amendment_2.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        self.amendment_2.reference_code = "GBSIEL/2025/0000002/P"
        self.amendment_2.save()
        EcjuQueryFactory(case=self.amendment_2, raised_by_user=self.gov_user)

        self.latest_case = self.amendment_2.create_amendment(self.exporter_user)
        self.amendment_2.refresh_from_db()
        self.latest_case.submitted_at = timezone.now()
        self.latest_case.reference_code = "GBSIEL/2025/0000003/P"
        self.latest_case.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        self.latest_case.save()
        self.latest_case.refresh_from_db()

    @parameterized.expand(["GBSIEL/2025/0000001/P", "GBSIEL/2025/0000002/P", "GBSIEL/2025/0000003/P"])
    def test_get_amendment_history(self, case_ref):

        case = Case.objects.get(reference_code=case_ref)
        url = reverse(
            "exporter_applications:history",
            kwargs={
                "pk": str(case.pk),
            },
        )

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_json = {
            "id": str(case.id),
            "reference_code": case.reference_code,
            "amendment_history": [
                {
                    "id": str(c.id),
                    "reference_code": c.reference_code,
                    "submitted_at": c.submitted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "status": {"status": c.status.status, "status_display": CaseStatusEnum.get_text(c.status.status)},
                    "ecju_query_count": c.case_ecju_query.all().count(),
                }
                for c in [self.latest_case, self.amendment_2, self.amendment_1]
            ],
        }
        self.assertEqual(response.json(), expected_json)

    def test_get_history_application_not_found(self):

        url = reverse(
            "exporter_applications:history",
            kwargs={
                "pk": str(uuid.uuid4()),
            },
        )
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_history_application_wrong_organisation(self):
        self.latest_case.organisation = OrganisationFactory()
        self.latest_case.save()

        url = reverse(
            "exporter_applications:history",
            kwargs={
                "pk": str(self.latest_case.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@pytest.fixture()
def application(organisation):
    return StandardApplicationFactory(organisation=organisation)


@pytest.fixture()
def document_data(application):
    return {
        "name": "my_file.jpg",
        "s3_key": "my_file.jpg",
        "size": 476,
        "description": "banana cake 1",
        "application": str(application.id),
    }


class TestApplicationDocuments:

    @pytest.mark.parametrize("application_factory", [StandardApplicationFactory, F680ApplicationFactory])
    def test_GET_success(self, application_factory, api_client, exporter_headers, organisation):

        my_application = application_factory(organisation=organisation)
        my_doc_1 = ApplicationDocumentFactory(application=my_application)
        my_doc_2 = ApplicationDocumentFactory(application=my_application)
        other_doc = ApplicationDocumentFactory()

        url = reverse(
            "exporter_applications:document",
            kwargs={
                "pk": str(my_application.pk),
            },
        )
        response = api_client.get(url, **exporter_headers)
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()

        assert response_json["count"] == 2

        result_doc_ids = [r["id"] for r in response_json["results"]]
        result_doc_applications = [r["application"] for r in response_json["results"]]

        assert [str(my_doc_1.id), str(my_doc_2.id)] == result_doc_ids
        assert str(my_application.id) in result_doc_applications
        assert str(other_doc.id) not in result_doc_ids

    def test_GET_application_not_found_404(self, api_client, exporter_headers):

        url = reverse(
            "exporter_applications:document",
            kwargs={
                "pk": str(uuid.uuid4()),
            },
        )
        response = api_client.get(url, **exporter_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_GET_application_documents_wrong_organisation_403(self, api_client, exporter_headers):
        other_application = StandardApplicationFactory(organisation=OrganisationFactory())

        url = reverse(
            "exporter_applications:document",
            kwargs={
                "pk": str(other_application.pk),
            },
        )
        response = api_client.get(url, exporter_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize("application_factory", [StandardApplicationFactory, F680ApplicationFactory])
    def test_POST_application_document(
        self, application_factory, api_client, exporter_headers, application, document_data, organisation
    ):

        my_application = application_factory(organisation=organisation)
        url = reverse(
            "exporter_applications:document",
            kwargs={
                "pk": str(my_application.pk),
            },
        )
        document_data["application"] = my_application.pk

        response = api_client.post(url, data=document_data, **exporter_headers)

        assert response.status_code == status.HTTP_201_CREATED
        response_document = response.json()

        response = api_client.get(url, **exporter_headers)

        expected = {
            **document_data,
            "id": response_document["id"],
            "application": str(my_application.id),
            "virus_scanned_at": None,
            "document_type": None,
            "safe": None,
            "created_at": response_document["created_at"],
            "updated_at": response_document["updated_at"],
        }

        assert response_document == expected

    def test_POST_application_document_create_audit(
        self, api_client, exporter_headers, exporter_user, application, document_data
    ):

        url = reverse(
            "exporter_applications:document",
            kwargs={
                "pk": str(application.pk),
            },
        )

        response = api_client.post(url, data=document_data, **exporter_headers)

        assert response.status_code == status.HTTP_201_CREATED

        audit = Audit.objects.get()

        assert audit.actor == exporter_user
        assert audit.target.id == application.id
        assert audit.verb == AuditType.UPLOAD_APPLICATION_DOCUMENT

        assert audit.payload == {"file_name": document_data["name"]}
