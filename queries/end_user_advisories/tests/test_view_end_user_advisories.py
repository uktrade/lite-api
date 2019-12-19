from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class EndUserAdvisoryViewTests(DataTestClient):
    def test_view_end_user_advisory_queries(self):
        """
        Ensure that the user can view all end user advisory queries
        """
        query = self.create_end_user_advisory("a note", "because I am unsure", self.organisation)

        response = self.client.get(reverse("queries:end_user_advisories:end_user_advisories"), **self.exporter_headers)
        response_data = response.json()["end_user_advisories"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response_data), 1)

        response_data = response_data[0]
        self.assertEqual(response_data["note"], query.note)
        self.assertEqual(response_data["reasoning"], query.reasoning)

        end_user_data = response_data["end_user"]
        self.assertEqual(end_user_data["sub_type"]["key"], query.end_user.sub_type)

        self.assertEqual(end_user_data["name"], query.end_user.name)
        self.assertEqual(end_user_data["website"], query.end_user.website)
        self.assertEqual(end_user_data["address"], query.end_user.address)
        self.assertEqual(end_user_data["country"]["id"], query.end_user.country.id)

    def test_view_end_user_advisory_query_on_organisation(self):
        """
        Ensure that the user can view an end user advisory query
        """
        query = self.create_end_user_advisory("a note", "because I am unsure", self.organisation)

        response = self.client.get(
            reverse("queries:end_user_advisories:end_user_advisory", kwargs={"pk": query.id}), **self.exporter_headers
        )
        response_data = response.json()["end_user_advisory"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["note"], query.note)
        self.assertEqual(response_data["reasoning"], query.reasoning)
        self.assertEqual(response_data["nature_of_business"], query.nature_of_business)
        self.assertEqual(response_data["contact_name"], query.contact_name)
        self.assertEqual(response_data["contact_email"], query.contact_email)
        self.assertEqual(response_data["contact_telephone"], query.contact_telephone)
        self.assertEqual(response_data["contact_job_title"], query.contact_job_title)

        end_user_data = response_data["end_user"]
        self.assertEqual(end_user_data["sub_type"]["key"], query.end_user.sub_type)
        self.assertEqual(end_user_data["name"], query.end_user.name)
        self.assertEqual(end_user_data["website"], query.end_user.website)
        self.assertEqual(end_user_data["address"], query.end_user.address)
        self.assertEqual(end_user_data["country"]["id"], query.end_user.country.id)
