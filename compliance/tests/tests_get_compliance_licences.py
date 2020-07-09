from django.urls import reverse

from cases.enums import CaseTypeEnum
from compliance.tests.factories import ComplianceSiteCaseFactory
from licences.enums import LicenceStatus
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


def _assert_response_data(self, response_data, licence):
    self.assertEqual(len(response_data), 1)
    self.assertEqual(response_data[0]["id"], str(licence.application_id))
    self.assertEqual(response_data[0]["reference_code"], licence.application.reference_code)
    self.assertEqual(response_data[0]["status"]["key"], licence.application.status.status)
    goods = licence.application.goods_type.all()
    self.assertEqual(len(response_data[0]["flags"]), 2)
    self.assertEqual(response_data[0]["flags"][0]["name"], goods[0].flags.all()[0].name)
    self.assertEqual(response_data[0]["flags"][1]["name"], goods[1].flags.all()[0].name)
    self.assertEqual(response_data[0]["flags"][0]["level"], goods[0].flags.all()[0].level)
    self.assertEqual(response_data[0]["flags"][1]["level"], goods[1].flags.all()[0].level)
    self.assertEqual(response_data[0]["flags"][0]["priority"], goods[0].flags.all()[0].priority)
    self.assertEqual(response_data[0]["flags"][1]["priority"], goods[1].flags.all()[0].priority)


class GetComplianceLicencesTests(DataTestClient):
    def test_get_compliance_OIEL_licences(self):
        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )
        application = self.create_open_application_case(self.organisation)
        licence = self.create_licence(application, status=LicenceStatus.ISSUED)

        url = reverse("compliance:licences", kwargs={"pk": compliance_case.id})
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        _assert_response_data(self, response_data, licence)

    def test_get_compliance_OICL_licences(self):
        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )
        application = self.create_open_application_case(self.organisation)
        application.case_type_id = CaseTypeEnum.OICL.id
        application.save()
        licence = self.create_licence(application, status=LicenceStatus.ISSUED)

        url = reverse("compliance:licences", kwargs={"pk": compliance_case.id})
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        _assert_response_data(self, response_data, licence)
