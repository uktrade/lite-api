from django.urls import reverse
from rest_framework import status

from cases.models import Case
from test_helpers.clients import DataTestClient


class CaseGetTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = Case.objects.get(application=self.standard_application)
        self.url = reverse('cases:case', kwargs={'pk': self.case.id})

    def test_case_returns_expected_third_party(self):
        """
        Given a case with a third party exists
        When the case is retrieved
        Then the third party is present in the json data
        """

        self.standard_application.third_parties.set([self.create_third_party('third party', self.organisation)])
        self.standard_application.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_third_party = self.standard_application.third_parties.first()
        actual_third_party = response_data['case']['application']['third_parties'][0]

        self._assert_party(expected_third_party, actual_third_party)

    def test_case_returns_expected_consignee(self):
        """
        Given a case with a consignee exists
        When the case is retrieved
        Then the consignee is present in the json data
        """

        self.standard_application.consignee = self.create_consignee('consignee', self.organisation)
        self.standard_application.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_consignee = self.standard_application.consignee
        actual_consignee = response_data['case']['application']['consignee']

        self._assert_party(expected_consignee, actual_consignee)

    def _assert_party(self, expected, actual):
        self.assertEqual(str(expected.id), actual['id'])
        self.assertEqual(str(expected.name), actual['name'])
        self.assertEqual(str(expected.country.name), actual['country']['name'])
        self.assertEqual(str(expected.website), actual['website'])
        self.assertEqual(str(expected.type), actual['type'])
        self.assertEqual(str(expected.organisation.id), actual['organisation'])
        self.assertEqual(str(expected.sub_type), actual['sub_type'])
