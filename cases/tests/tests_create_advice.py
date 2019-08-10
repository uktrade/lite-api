from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.enums import AdviceType
from cases.models import Case, Advice
from test_helpers.clients import DataTestClient


class CreateCaseAdviceTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.exporter_user.organisation)
        self.standard_case = Case.objects.get(application=self.standard_application)

        self.open_application = self.create_open_application(self.exporter_user.organisation)
        self.open_case = Case.objects.get(application=self.open_application)

        self.standard_case_url = reverse('cases:case_advice', kwargs={'pk': self.standard_case.id})
        self.open_case_url = reverse('cases:case_advice', kwargs={'pk': self.open_case.id})

    @parameterized.expand([
        [AdviceType.APPROVE],
        [AdviceType.PROVISO],
        [AdviceType.REFUSE],
        [AdviceType.NO_LICENCE_REQUIRED],
        [AdviceType.NOT_APPLICABLE],
    ])
    def test_create_standard_case_advice(self, advice_type):
        """
        Tests that a gov user can create an approval/proviso/refuse/nlr/not_applicable
        piece of advice for a standard case
        """
        data = {
            'type': advice_type,
            'advice': 'I Am Easy to Find',
            'note': 'I Am Easy to Find',
            'end_user': str(self.standard_application.end_user.id),
            'ultimate_end_users': [str(self.standard_application.end_user.id)],
            'goods': [str(good_on_application.good.id) for good_on_application in self.standard_application.goods.all()],
            'proviso': 'I Am Easy to Proviso',
            'denial_reasons': ['1a', '1b', '1c'],
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=data)
        response_data = response.json()['advice']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response_data['advice'], data['advice'])
        self.assertEqual(response_data['note'], data['note'])
        self.assertEqual(response_data['type']['key'], data['type'])
        self.assertEqual(response_data['goods'], data['goods'])
        self.assertEqual(response_data['end_user'], data['end_user'])

        advice_object = Advice.objects.get()

        # Ensure that proviso details aren't added unless the type sent is PROVISO
        if advice_type != AdviceType.PROVISO:
            self.assertTrue('proviso' not in response_data)
            self.assertEqual(advice_object.proviso, None)
        else:
            self.assertEqual(response_data['proviso'], data['proviso'])
            self.assertEqual(advice_object.proviso, data['proviso'])

        # Ensure that refusal details aren't added unless the type sent is REFUSE
        if advice_type != AdviceType.REFUSE:
            self.assertTrue('denial_reasons' not in response_data)
            self.assertEqual(advice_object.denial_reasons.count(), 0)
        else:
            self.assertEqual(response_data['denial_reasons'], data['denial_reasons'])
            self.assertEqual(self.convert_queryset_to_str(advice_object.denial_reasons.values_list('id', flat=True)),
                             data['denial_reasons'])

    @parameterized.expand([
        [AdviceType.APPROVE],
        [AdviceType.PROVISO],
        [AdviceType.REFUSE],
        [AdviceType.NO_LICENCE_REQUIRED],
        [AdviceType.NOT_APPLICABLE],
    ])
    def test_create_open_case_advice(self, advice_type):
        """
        Tests that a gov user can create an approval/proviso/refuse/nlr/not_applicable
        piece of advice for an open case
        """
        data = {
            'type': advice_type,
            'advice': 'I Am Easy to Find',
            'note': 'I Am Easy to Find',
            'countries': ['GB'],
            'goods_types': [str(self.create_goods_type('application', self.open_application).id)],
            'proviso': 'I Am Easy to Proviso',
            'denial_reasons': ['1a', '1b', '1c'],
        }

        response = self.client.post(self.open_case_url, **self.gov_headers, data=data)
        response_data = response.json()['advice']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response_data['advice'], data['advice'])
        self.assertEqual(response_data['note'], data['note'])
        self.assertEqual(response_data['type']['key'], data['type'])
        self.assertEqual(response_data['goods_types'], data['goods_types'])
        self.assertEqual(response_data['countries'], data['countries'])

        advice_object = Advice.objects.get()

        # Ensure that proviso details aren't added unless the type sent is PROVISO
        if advice_type != AdviceType.PROVISO:
            self.assertTrue('proviso' not in response_data)
            self.assertEqual(advice_object.proviso, None)
        else:
            self.assertEqual(response_data['proviso'], data['proviso'])
            self.assertEqual(advice_object.proviso, data['proviso'])

        # Ensure that refusal details aren't added unless the type sent is REFUSE
        if advice_type != AdviceType.REFUSE:
            self.assertTrue('denial_reasons' not in response_data)
            self.assertEqual(advice_object.denial_reasons.count(), 0)
        else:
            self.assertEqual(response_data['denial_reasons'], data['denial_reasons'])
            self.assertEqual(self.convert_queryset_to_str(advice_object.denial_reasons.values_list('id', flat=True)),
                             data['denial_reasons'])
