from django.test import tag
from django.urls import reverse
from rest_framework import status

from applications.models import CountryOnApplication
from test_helpers.clients import DataTestClient


class ContractTypeOnCountryTests(DataTestClient):
    @tag("2146")
    def test_set_contract_type_on_country_on_application_success(self):
        application = self.create_open_application_case(self.organisation)

        data = {
            "countries": ["GB"],
            "contract_types": ["navy"],
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.post(url, data, **self.exporter_headers)
        coa = CountryOnApplication.objects.get(country_id="GB", application=application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(coa.contract_types, ["navy"])

    @tag("2146")
    def test_set_multiple_contract_types_on_country_on_application_success(self):
        application = self.create_open_application_case(self.organisation)
        CountryOnApplication(country_id="FR", application=application).save()

        data = {
            "countries": ["GB", "FR"],
            "contract_types": ["navy", "army"],
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.post(url, data, **self.exporter_headers)
        coa_gb = CountryOnApplication.objects.get(country_id="GB", application=application)
        coa_fr = CountryOnApplication.objects.get(country_id="FR", application=application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(coa_gb.contract_types, ["navy", "army"])
        self.assertEqual(coa_fr.contract_types, ["navy", "army"])
