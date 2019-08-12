from django.urls import reverse
from rest_framework import status

from cases.enums import AdviceType
from cases.models import Case, Advice
from test_helpers.clients import DataTestClient


class ViewCaseAdviceTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.exporter_user.organisation)
        self.standard_case = Case.objects.get(application=self.standard_application)

        self.open_application = self.create_open_application(self.exporter_user.organisation)
        self.open_case = Case.objects.get(application=self.open_application)

        self.standard_case_url = reverse('cases:case_advice', kwargs={'pk': self.standard_case.id})
        self.open_case_url = reverse('cases:case_advice', kwargs={'pk': self.open_case.id})

    def test_view_standard_case_advice(self):
        """
        Tests that a gov user can see all advice for a standard case
        """
        advice = Advice(case=self.standard_case,
                        user=self.gov_user,
                        type=AdviceType.PROVISO,
                        proviso='I Am Easy to Proviso',
                        advice='This is advice',
                        note='This is a note',
                        end_user=self.standard_application.end_user, )
        advice.ultimate_end_users.set([self.standard_application.end_user])
        advice.goods.set([x.good for x in self.standard_application.goods.all()])
        advice.save()

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()['advice']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)

    def test_view_open_case_advice(self):
        """
        Tests that a gov user can see all advice for an open case
        """
        advice = Advice(case=self.open_case,
                        user=self.gov_user,
                        type=AdviceType.PROVISO,
                        proviso='I Am Easy to Proviso',
                        advice='This is advice',
                        note='This is a note',
                        end_user=self.standard_application.end_user, )
        advice.ultimate_end_users.set([self.standard_application.end_user])
        advice.goods.set([x.good for x in self.standard_application.goods.all()])
        advice.save()

        response = self.client.get(self.open_case_url, **self.gov_headers)
        response_data = response.json()['advice']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
