from django.urls import reverse
from rest_framework import status

from api.compliance.models import CompliancePerson
from api.compliance.tests.factories import ComplianceVisitCaseFactory, PeoplePresentFactory
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class ComplianceVisitCaseTests(DataTestClient):
    def test_get_people_present(self):
        comp_case = ComplianceVisitCaseFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )
        person1 = PeoplePresentFactory(visit_case=comp_case)
        person2 = PeoplePresentFactory(visit_case=comp_case)

        url = reverse("compliance:people_present", kwargs={"pk": comp_case.id})
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        for person in response_data:
            self.assertIn(person["id"], [str(person1.id), str(person2.id)])

    def test_create_people_present(self):
        comp_case = ComplianceVisitCaseFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )

        post_person = {"name": "joe", "job_title": "fisher"}
        data = {"people_present": [post_person]}

        url = reverse("compliance:people_present", kwargs={"pk": comp_case.id})
        response = self.client.post(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        person = response_data["people_present"][0]
        self.assertEqual(person["name"], post_person["name"])
        self.assertEqual(person["job_title"], post_person["job_title"])

    def test_update_people_present(self):
        comp_case = ComplianceVisitCaseFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )
        person = PeoplePresentFactory(visit_case=comp_case)

        data = {"name": "new_name", "job_title": "anotherjob"}

        url = reverse("compliance:person_present", kwargs={"pk": person.id})
        response = self.client.patch(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["name"], data["name"])
        self.assertEqual(response_data["job_title"], data["job_title"])

    def test_delete_people_present(self):
        comp_case = ComplianceVisitCaseFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )
        person = PeoplePresentFactory(visit_case=comp_case)

        self.assertTrue(CompliancePerson.objects.exists())
        url = reverse("compliance:person_present", kwargs={"pk": person.id})
        response = self.client.delete(url, **self.gov_headers)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CompliancePerson.objects.exists())
