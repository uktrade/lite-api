from django.urls import reverse
from rest_framework import status

from api.applications.tests.factories import (
    StandardApplicationFactory,
    PartyOnApplicationFactory,
)
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient


class TestApplicationPartyView(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory(organisation=self.organisation)
        self.case_statuses = [
            case_status.status
            for case_status in CaseStatus.objects.all()
            if case_status.status not in ["draft", "applicant_editing"]
        ]
        self.data = {"name": "End user", "address": "1 Example Street", "country": {"id": "FR", "name": "France"}}
        self.party_on_application = PartyOnApplicationFactory(application=self.application)
        self.url = reverse(
            "applications:party",
            kwargs={"pk": str(self.application.pk), "party_pk": str(self.party_on_application.party.pk)},
        )

    def test_draft_application_can_update_party_detail(self):
        self.application.status = CaseStatus.objects.get(status="draft")
        self.application.save()
        response = self.client.put(self.url, **self.exporter_headers, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_editing_application_can_update_party_detail(self):
        self.application.status = CaseStatus.objects.get(status="applicant_editing")
        self.application.save()
        response = self.client.put(self.url, **self.exporter_headers, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_status_cannot_update_party_detail(self):
        for case_status in self.case_statuses:
            self.application.status = CaseStatus.objects.get(status=case_status)
            self.application.save()
            response = self.client.put(self.url, **self.exporter_headers, data=self.data)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(
                response.json(),
                {
                    "errors": [
                        f"The {self.party_on_application.party.type} party cannot be edited in {case_status} status"
                    ]
                },
            )
