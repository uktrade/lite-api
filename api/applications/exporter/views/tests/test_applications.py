import uuid
from django.utils import timezone
from pytz import timezone as tz

from api.cases.tests.factories import EcjuQueryFactory
from parameterized import parameterized

from django.urls import reverse
from rest_framework import status

from api.applications.tests.factories import StandardApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.cases.models import Case, Queue
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


class TestApplicationHistory(DataTestClient):

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
                    "submitted_at": c.submitted_at.astimezone(tz("UTC")).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
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
