from django.urls import reverse
from rest_framework import status

from api.applications.models import CountryOnApplication
from cases.libraries.get_flags import get_ordered_flags
from api.flags.tests.factories import FlagFactory
from lite_content.lite_api import strings
from api.staticdata.countries.models import Country
from test_helpers.clients import DataTestClient


class ContractTypeOnCountryTests(DataTestClient):
    def test_set_contract_type_on_country_on_application_success(self):
        application = self.create_draft_open_application(self.organisation)

        data = {"countries": ["FR"], "contract_types": ["navy"], "other_contract_type_text": None}

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        coa = CountryOnApplication.objects.get(country_id="FR", application=application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(coa.contract_types, ["navy"])

    def test_set_multiple_contract_types_on_country_on_application_success(self):
        application = self.create_draft_open_application(self.organisation)
        # Add ES as an additional country (FR already present on draft open applications)
        CountryOnApplication(country_id="ES", application=application).save()

        data = {"countries": ["FR", "ES"], "contract_types": ["navy", "army"], "other_contract_type_text": ""}

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        coa_gb = CountryOnApplication.objects.get(country_id="ES", application=application)
        coa_fr = CountryOnApplication.objects.get(country_id="FR", application=application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(set(coa_gb.contract_types).issubset({"navy", "army"}))
        self.assertTrue(set(coa_fr.contract_types).issubset({"navy", "army"}))

    def test_set_other_contract_type_without_text_on_country_on_application_failure(self):
        application = self.create_draft_open_application(self.organisation)

        data = {"countries": ["FR"], "contract_types": ["other_contract_type"], "other_contract_type_text": ""}

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_other_contract_type_on_country_on_application_success(self):
        application = self.create_draft_open_application(self.organisation)

        contract_types = ["navy", "other_contract_type"]
        other_text = "This is some text"

        data = {
            "countries": ["FR"],
            "contract_types": contract_types,
            "other_contract_type_text": other_text,
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        coa = CountryOnApplication.objects.get(country_id="FR", application=application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(set(coa.contract_types).issubset(set(contract_types)))
        self.assertEqual(coa.other_contract_type_text, other_text)

    def test_set_other_contract_text_without_other_on_country_on_application_success_other_text_not_stored(self):
        application = self.create_draft_open_application(self.organisation)

        contract_types = ["navy", "army"]
        other_text = "This is some text"

        data = {
            "countries": ["FR"],
            "contract_types": contract_types,
            "other_contract_type_text": other_text,
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        coa = CountryOnApplication.objects.get(country_id="FR", application=application)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(set(coa.contract_types).issubset(set(contract_types)))
        self.assertEqual(coa.other_contract_type_text, None)

    def test_no_contract_types_failure(self):
        application = self.create_draft_open_application(self.organisation)

        data = {
            "countries": ["FR"],
            "contract_types": [],
            "other_contract_type_text": "",
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_contract_types_field_failure(self):
        application = self.create_draft_open_application(self.organisation)

        data = {
            "countries": ["FR"],
            "other_contract_type_text": "",
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})

        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_removing_other_clears_text(self):
        application = self.create_draft_open_application(self.organisation)

        data = {
            "countries": ["FR"],
            "contract_types": ["navy"],
            "other_contract_type_text": "",
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})
        coa = CountryOnApplication.objects.get(country_id="FR", application=application)
        coa.other_contract_type_text = "this is text"
        coa.save()
        self.client.put(url, data, **self.exporter_headers)

        coa.refresh_from_db()
        self.assertEqual(coa.other_contract_type_text, None)

    def test_flags_are_returned_correctly(self):
        application = self.create_draft_open_application(self.organisation)
        falg = FlagFactory(team=self.team)
        flag = FlagFactory(team=self.team)
        Country.objects.get(id="FR").flags.set([falg.id, flag.id])

        data = {
            "countries": ["FR"],
            "contract_types": ["navy", "army"],
            "other_contract_type_text": "",
        }

        url = reverse("applications:contract_types", kwargs={"pk": application.id})
        self.client.put(url, data, **self.exporter_headers)

        ordered_flags = get_ordered_flags(application, self.team)

        self.assertIn("Navy", str(ordered_flags))
        self.assertIn("Army", str(ordered_flags))

    def test_submit_without_sectors_on_each_country_failure(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        application = self.create_draft_open_application(self.organisation)

        url = reverse("applications:application_submit", kwargs={"pk": application.id})
        response = self.client.put(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(strings.Applications.Open.INCOMPLETE_CONTRACT_TYPES, response.json()["errors"]["contract_types"])
