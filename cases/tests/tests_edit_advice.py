from django.urls import reverse

from cases.enums import AdviceType
from cases.models import Case, Advice
from test_helpers.clients import DataTestClient


class EditCaseAdviceTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.exporter_user.organisation)
        self.standard_case = Case.objects.get(application=self.standard_application)

        self.open_application = self.create_open_application(self.exporter_user.organisation)
        self.open_case = Case.objects.get(application=self.open_application)

        self.standard_case_url = reverse('cases:case_advice', kwargs={'pk': self.standard_case.id})
        self.open_case_url = reverse('cases:case_advice', kwargs={'pk': self.open_case.id})

    # def test_edit_standard_case_advice_twice_only_shows_once(self):
    #     """
    #     Tests that a gov user cannot create two pieces of advice on the same
    #     case item (be that a good or destination)
    #     """
    #     data = {
    #         'type': AdviceType.APPROVE,
    #         'advice': 'I Am Easy to Find',
    #         'note': 'I Am Easy to Find',
    #         'countries': ['GB'],
    #         'goods_types': [str(self.create_goods_type('application', self.open_application).id)],
    #     }
    #
    #     self.client.post(self.open_case_url, **self.gov_headers, data=data)
    #     self.client.post(self.open_case_url, **self.gov_headers, data=data)
    #
    #     # Assert that there's only one piece of advice
    #     self.assertEqual(Advice.objects.count(), 1)
