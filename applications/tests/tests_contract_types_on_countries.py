from django.test import tag
from django.urls import reverse
from rest_framework import status

from applications.models import CountryOnApplication
from cases.libraries.get_flags import get_ordered_flags
from flags.tests.factories import FlagFactory
from static.countries.models import Country
from test_helpers.clients import DataTestClient


class ContractTypeOnCountryTests(DataTestClient):
    @tag("2146")
    def test_set_contract_type_on_country_on_application_success(self):
        application = self.create_open_application_case(self.organisation)

        data = {"countries": ["GB"], "contract_types": ["navy"], "other_contract_type_text": None}

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        coa = CountryOnApplication.objects.get(country_id="GB", application=application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(coa.contract_types, ["navy"])

    @tag("2146")
    def test_set_multiple_contract_types_on_country_on_application_success(self):
        application = self.create_open_application_case(self.organisation)
        CountryOnApplication(country_id="FR", application=application).save()

        data = {"countries": ["GB", "FR"], "contract_types": ["navy", "army"], "other_contract_type_text": ""}

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        coa_gb = CountryOnApplication.objects.get(country_id="GB", application=application)
        coa_fr = CountryOnApplication.objects.get(country_id="FR", application=application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(set(coa_gb.contract_types).issubset({"navy", "army"}))
        self.assertTrue(set(coa_fr.contract_types).issubset({"navy", "army"}))

    @tag("2146", "errors")
    def test_set_other_contract_type_without_text_on_country_on_application_failure(self):
        application = self.create_open_application_case(self.organisation)

        data = {"countries": ["GB"], "contract_types": ["other_contract_type"], "other_contract_type_text": ""}

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag("2146")
    def test_set_other_contract_type_on_country_on_application_success(self):
        application = self.create_open_application_case(self.organisation)

        contract_types = ["navy", "other_contract_type"]
        other_text = "This is some text"

        data = {
            "countries": ["GB"],
            "contract_types": contract_types,
            "other_contract_type_text": other_text,
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        coa = CountryOnApplication.objects.get(country_id="GB", application=application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(set(coa.contract_types).issubset(set(contract_types)))
        self.assertEqual(coa.other_contract_type_text, other_text)

    @tag("2146", "no-contract")
    def test_no_contract_types_failure(self):
        application = self.create_open_application_case(self.organisation)

        data = {
            "countries": ["GB"],
            "contract_types": [],
            "other_contract_type_text": "",
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag("2146", "no-field", "errors")
    def test_no_contract_types_field_failure(self):
        application = self.create_open_application_case(self.organisation)

        data = {
            "countries": ["GB"],
            "other_contract_type_text": "",
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag("2146", "clear")
    def test_removing_other_clears_text(self):
        application = self.create_open_application_case(self.organisation)

        data = {
            "countries": ["GB"],
            "contract_types": ["navy"],
            "other_contract_type_text": "",
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})
        coa = CountryOnApplication.objects.get(country_id="GB", application=application)
        coa.other_contract_type_text = "this is text"
        coa.save()
        self.client.put(url, data, **self.exporter_headers)

        coa.refresh_from_db()
        self.assertEqual(coa.other_contract_type_text, None)

    @tag("2146", "flags")
    def test_flags_are_returned_correctly(self):
        application = self.create_open_application_case(self.organisation)
        falg = FlagFactory(team=self.team)
        flag = FlagFactory(team=self.team)
        Country.objects.get(id="GB").flags.set([falg.id, flag.id])

        data = {
            "countries": ["GB"],
            "contract_types": ["navy"],
            "other_contract_type_text": "",
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})
        self.client.put(url, data, **self.exporter_headers)

        get_ordered_flags(application, self.team)
