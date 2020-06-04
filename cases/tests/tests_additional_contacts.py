from django.urls import reverse
from faker import Faker
from rest_framework import status

from parties.enums import PartyType
from parties.models import Party
from test_helpers.clients import DataTestClient
from test_helpers.helpers import generate_key_value_pair, generate_country_dict


class AdditionalContacts(DataTestClient):
    def setUp(self):
        super().setUp()
        case = self.create_standard_application_case(self.organisation)
        self.url = reverse("cases:additional_contacts", kwargs={"pk": case.id})
        self.fake = Faker()
        self.data = {
            "name": self.fake.name(),
            "phone_number": self.fake.phone_number(),
            "email": self.fake.email(),
            "details": self.fake.paragraph(nb_sentences=3, variable_nb_sentences=True, ext_word_list=None),
            "address": self.fake.address(),
            "country": "GB",
        }

    def test_view_additional_contacts(self):
        additional_contact = self.create_party(self.fake.name(), self.organisation, PartyType.ADDITIONAL_CONTACT)

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()[0],
            {
                "id": str(additional_contact.id),
                "name": additional_contact.name,
                "phone_number": additional_contact.phone_number,
                "email": additional_contact.email,
                "details": additional_contact.details,
                "address": additional_contact.address,
                "organisation": str(additional_contact.organisation.id),
                "country": generate_country_dict(additional_contact.country),
                "type": generate_key_value_pair(additional_contact.type, PartyType.choices),
            },
        )

    def test_create_additional_contact_as_internal_success(self):
        response = self.client.post(self.url, self.data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        party = Party.objects.get(name=self.data["name"])
        self.assertEqual(party.phone_number, self.data["phone_number"])
        self.assertEqual(party.email, self.data["email"])
        self.assertEqual(party.details, self.data["details"])
        self.assertEqual(party.address, self.data["address"])
        self.assertEqual(party.country.id, self.data["country"])

    def test_create_additional_contact_as_exporter_failure(self):
        party_count = Party.objects.count()

        response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Party.objects.count(), party_count)


class CaseApplicant(DataTestClient):
    def test_get_case_applicant(self):
        case = self.create_standard_application_case(self.organisation)
        self.url = reverse("cases:case_applicant", kwargs={"pk": case.id})

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["name"], case.submitted_by.first_name + " " + case.submitted_by.last_name)
        self.assertEqual(response_data["email"], case.submitted_by.email)
