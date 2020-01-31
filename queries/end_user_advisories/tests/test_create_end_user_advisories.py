from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.models import Case
from parties.enums import PartyType
from test_helpers.clients import DataTestClient


class EndUserAdvisoryCreateTests(DataTestClient):
    url = reverse("queries:end_user_advisories:end_user_advisories")

    def test_create_end_user_advisory_query(self):
        """
        Ensure that a user can create an end user advisory, and that it creates a case
        when doing so
        """
        data = {
            "end_user": {
                "sub_type": "government",
                "name": "Ada",
                "website": "https://gov.uk",
                "address": "123",
                "country": "GB",
                "type": PartyType.END_USER,
            },
            "note": "I Am Easy to Find",
            "reasoning": "Lack of hairpin turns",
            "nature_of_business": "guns",
            "contact_name": "Steven",
            "contact_email": "steven@gov.com",
            "contact_job_title": "director",
            "contact_telephone": "0123456789",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()["end_user_advisory"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["note"], data["note"])
        self.assertEqual(response_data["reasoning"], data["reasoning"])
        self.assertEqual(response_data["contact_email"], data["contact_email"])
        self.assertEqual(response_data["contact_telephone"], data["contact_telephone"])
        self.assertEqual(response_data["contact_job_title"], data["contact_job_title"])

        end_user_data = response_data["end_user"]
        self.assertEqual(end_user_data["sub_type"]["key"], data["end_user"]["sub_type"])
        self.assertEqual(end_user_data["name"], data["end_user"]["name"])
        self.assertEqual(end_user_data["website"], data["end_user"]["website"])
        self.assertEqual(end_user_data["address"], data["end_user"]["address"])
        self.assertEqual(end_user_data["country"]["id"], data["end_user"]["country"])
        self.assertEqual(Case.objects.count(), 1)

    def test_create_copied_end_user_advisory_query(self):
        """
        Ensure that a user can duplicate an end user advisory, it links to the previous
        query and that it creates a case when doing so
        """
        query = self.create_end_user_advisory("Advisory", "", self.organisation)
        data = {
            "end_user": {
                "sub_type": "government",
                "name": "Ada",
                "website": "https://gov.uk",
                "address": "123",
                "country": "GB",
                "type": PartyType.END_USER,
            },
            "note": "I Am Easy to Find",
            "reasoning": "Lack of hairpin turns",
            "copy_of": query.id,
            "nature_of_business": "guns",
            "contact_name": "Steven",
            "contact_email": "steven@gov.com",
            "contact_job_title": "director",
            "contact_telephone": "0123456789",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()["end_user_advisory"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["note"], data["note"])
        self.assertEqual(response_data["reasoning"], data["reasoning"])
        self.assertEqual(response_data["copy_of"], str(data["copy_of"]))

        end_user_data = response_data["end_user"]
        self.assertEqual(end_user_data["sub_type"]["key"], data["end_user"]["sub_type"])
        self.assertEqual(end_user_data["name"], data["end_user"]["name"])
        self.assertEqual(end_user_data["website"], data["end_user"]["website"])
        self.assertEqual(end_user_data["address"], data["end_user"]["address"])
        self.assertEqual(end_user_data["country"]["id"], data["end_user"]["country"])
        self.assertEqual(Case.objects.count(), 2)

    @parameterized.expand(
        [
            ("com", "person", "http://gov.co.uk", "place street", "GB", "", "",),  # invalid end user type
            ("commercial", "", "", "nowhere", "GB", "", ""),  # name is empty
            ("government", "abc", "abc", "nowhere", "GB", "", "",),  # invalid web address
            ("government", "abc", "", "", "GB", "", ""),  # empty address
            ("government", "abc", "", "nowhere", "ALP", "", ""),  # invalid country code
            ("", "", "", "", "", "", ""),  # empty dataset
        ]
    )
    def test_create_end_user_advisory_query_failure(
        self, end_user_type, name, website, address, country, note, reasoning
    ):
        data = {
            "end_user": {
                "type": end_user_type,
                "name": name,
                "website": website,
                "address": address,
                "country": country,
            },
            "note": note,
            "reasoning": reasoning,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_end_user_advisory_query_for_organisation_failure(self):
        """
        Fail to create organisation advisory with missing fields
        """
        data = {
            "end_user": {
                "sub_type": "commercial",
                "name": "Ada",
                "website": "https://gov.uk",
                "address": "123",
                "country": "GB",
                "type": PartyType.END_USER,
            },
            "note": "I Am Easy to Find",
            "reasoning": "Lack of hairpin turns",
            "contact_email": "steven@gov.com",
            "contact_telephone": "0123456789",
            "nature_of_business": "",
            "contact_name": "",
            "contact_job_title": "",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()["errors"]

        self.assertEqual(errors.get("nature_of_business"), ["This field may not be blank"])
        self.assertEqual(errors.get("contact_name"), ["This field may not be blank"])
        self.assertEqual(errors.get("contact_job_title"), ["This field may not be blank"])

    def test_create_end_user_advisory_query_for_government_failure(self):
        """
        Fail to create gov advisory with missing fields
        """
        data = {
            "end_user": {
                "sub_type": "commercial",
                "name": "Ada",
                "website": "https://gov.uk",
                "address": "123",
                "country": "GB",
                "type": PartyType.END_USER,
            },
            "note": "I Am Easy to Find",
            "reasoning": "Lack of hairpin turns",
            "contact_email": "steven@gov.com",
            "contact_telephone": "0123456789",
            "contact_name": "",
            "contact_job_title": "",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()["errors"]

        self.assertEqual(errors.get("contact_name"), ["This field may not be blank"])
        self.assertEqual(errors.get("contact_job_title"), ["This field may not be blank"])

    def test_create_end_user_advisory_query_for_government(self):
        """
        Successfully creates gov advisory
        """
        data = {
            "end_user": {
                "sub_type": "government",
                "name": "Ada",
                "website": "https://gov.uk",
                "address": "123",
                "country": "GB",
                "type": PartyType.END_USER
            },
            "note": "I Am Easy to Find",
            "reasoning": "Lack of hairpin turns",
            "contact_email": "steven@gov.com",
            "contact_telephone": "0123456789",
            "contact_name": "steven",
            "contact_job_title": "director",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_end_user_advisory_query_for_individual(self):
        """
        Successfully create individual advisory
        """
        data = {
            "end_user": {
                "sub_type": "individual",
                "name": "Ada",
                "website": "https://gov.uk",
                "address": "123",
                "country": "GB",
                "type": PartyType.END_USER,
            },
            "note": "I Am Easy to Find",
            "reasoning": "Lack of hairpin turns",
            "contact_email": "steven@gov.com",
            "contact_telephone": "0123456789",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()["end_user_advisory"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["note"], data["note"])
        self.assertEqual(response_data["reasoning"], data["reasoning"])
        self.assertEqual(response_data["contact_email"], data["contact_email"])
        self.assertEqual(response_data["contact_telephone"], data["contact_telephone"])

        end_user_data = response_data["end_user"]
        self.assertEqual(end_user_data["sub_type"]["key"], data["end_user"]["sub_type"])
        self.assertEqual(end_user_data["name"], data["end_user"]["name"])
        self.assertEqual(end_user_data["website"], data["end_user"]["website"])
        self.assertEqual(end_user_data["address"], data["end_user"]["address"])
        self.assertEqual(end_user_data["country"]["id"], data["end_user"]["country"])
        self.assertEqual(Case.objects.count(), 1)
