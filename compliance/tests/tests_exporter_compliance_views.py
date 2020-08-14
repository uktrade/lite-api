from rest_framework import status
from rest_framework.reverse import reverse

from compliance.tests.factories import ComplianceSiteCaseFactory, ComplianceVisitCaseFactory
from api.organisations.tests.factories import SiteFactory
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from users.models import UserOrganisationRelationship


class ComplianceExporterViewTests(DataTestClient):
    def compare_compliance_case_in_list(self, data, case, site):
        self.assertEqual(data["id"], str(case.id))
        self.assertEqual(data["site_name"], str(site.name))
        self.assertEqual(data["address"]["address_line_1"], site.address.address_line_1)
        self.assertEqual(data["address"]["address_line_2"], site.address.address_line_2)
        self.assertEqual(data["address"]["city"], site.address.city)
        self.assertEqual(data["address"]["region"], site.address.region)
        self.assertEqual(data["address"]["postcode"], site.address.postcode)
        self.assertEqual(data["address"]["country"]["id"], site.address.country.id)

    def test_get_exporter_compliance_case_list_1(self):
        comp_case_1 = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        site_2 = SiteFactory(organisation=self.organisation)
        comp_case_2 = ComplianceSiteCaseFactory(
            organisation=self.organisation, site=site_2, status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        site_3 = SiteFactory(organisation=self.organisation)
        comp_case_3 = ComplianceSiteCaseFactory(
            organisation=self.organisation, site=site_3, status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

        url = reverse("compliance:exporter_site_list")
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 3)

        comp_cases = [comp_case_1, comp_case_2, comp_case_3]
        comp_case_ids = [str(comp_case.id) for comp_case in comp_cases]
        response_data_ids = [data["id"] for data in response_data]

        self.assertEqual(set(comp_case_ids), set(response_data_ids))

        comp_case_1_response_data = response_data[response_data_ids.index(str(comp_case_1.id))]
        comp_case_2_response_data = response_data[response_data_ids.index(str(comp_case_2.id))]
        comp_case_3_response_data = response_data[response_data_ids.index(str(comp_case_3.id))]

        self.compare_compliance_case_in_list(comp_case_1_response_data, comp_case_1, self.organisation.primary_site)
        self.compare_compliance_case_in_list(comp_case_2_response_data, comp_case_2, site_2)
        self.compare_compliance_case_in_list(comp_case_3_response_data, comp_case_3, site_3)

    def test_get_exporter_compliance_case_list_2(self):
        user_org_relationship = UserOrganisationRelationship.objects.get(user=self.exporter_user)
        comp_case_1 = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )
        self.organisation.primary_site.users.add(user_org_relationship)

        site_2 = SiteFactory(organisation=self.organisation)
        site_2.users.add(user_org_relationship)
        comp_case_2 = ComplianceSiteCaseFactory(
            organisation=self.organisation, site=site_2, status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        site_3 = SiteFactory(organisation=self.organisation)
        comp_case_3 = ComplianceSiteCaseFactory(
            organisation=self.organisation, site=site_3, status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        url = reverse("compliance:exporter_site_list")
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 2)

        self.compare_compliance_case_in_list(response_data[0], comp_case_1, self.organisation.primary_site)
        self.compare_compliance_case_in_list(response_data[1], comp_case_2, site_2)

    def test_exporter_site_details(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        comp_case_1 = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        url = reverse("compliance:exporter_site_detail", kwargs={"pk": comp_case_1.id})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()

        self.assertEqual(response_data["id"], str(comp_case_1.id))
        self.assertEqual(response_data["reference_code"], comp_case_1.reference_code)
        self.assertEqual(response_data["site_name"], comp_case_1.site.name)
        self.assertEqual(response_data["address"]["address_line_1"], comp_case_1.site.address.address_line_1)
        self.assertEqual(response_data["address"]["address_line_2"], comp_case_1.site.address.address_line_2)
        self.assertEqual(response_data["address"]["city"], comp_case_1.site.address.city)
        self.assertEqual(response_data["address"]["region"], comp_case_1.site.address.region)
        self.assertEqual(response_data["address"]["postcode"], comp_case_1.site.address.postcode)
        self.assertEqual(response_data["address"]["country"]["id"], comp_case_1.site.address.country.id)
        self.assertEqual(response_data["is_primary_site"], True)

    def compare_compliance_visit_list_details(self, data, case):
        self.assertEqual(data["id"], str(case.id))
        self.assertEqual(data["reference_code"], case.reference_code)
        self.assertEqual(data["visit_date"], case.visit_date.strftime("%Y-%m-%d"))
        self.assertEqual(data["exporter_user_notification_count"], 0)

        if case.case_officer:
            self.assertEqual(data["case_officer_first_name"], case.case_officer.first_name)
            self.assertEqual(data["case_officer_last_name"], case.case_officer.last_name)
        else:
            self.assertEqual(data["case_officer_first_name"], None)
            self.assertEqual(data["case_officer_last_name"], None)

    def test_exporter_get_compliance_visits(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        comp_visit_1 = ComplianceVisitCaseFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )
        comp_site_case = comp_visit_1.site_case

        comp_visit_2 = ComplianceVisitCaseFactory(
            organisation=self.organisation,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
            site_case=comp_site_case,
        )
        comp_visit_2.case_officer = self.gov_user
        comp_visit_2.save()

        url = reverse("compliance:exporter_visit_case_list", kwargs={"pk": comp_site_case.id})
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 2)

        self.compare_compliance_visit_list_details(response_data[0], comp_visit_1)
        self.compare_compliance_visit_list_details(response_data[1], comp_visit_2)

    def test_exporter_get_visit_details(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        comp_visit_1 = ComplianceVisitCaseFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )
        comp_visit_1.case_officer = self.gov_user
        comp_visit_1.save()

        url = reverse("compliance:exporter_visit_case_detail", kwargs={"pk": comp_visit_1.id})
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()

        self.assertEqual(response_data["id"], str(comp_visit_1.id))
        self.assertEqual(response_data["reference_code"], comp_visit_1.reference_code)
        self.assertEqual(response_data["visit_date"], comp_visit_1.visit_date.strftime("%Y-%m-%d"))
        self.assertEqual(response_data["case_officer_first_name"], comp_visit_1.case_officer.first_name)
        self.assertEqual(response_data["case_officer_last_name"], comp_visit_1.case_officer.last_name)
