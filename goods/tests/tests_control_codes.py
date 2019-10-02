

# valid test (single good, multiple goods) (NLR and control_code) # test flags are removed from good
# fail tests (invalid pk: [single/multiple], controlled good and missing control code, missing comment, missing)
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from picklists.enums import PicklistType, PickListStatus
from test_helpers.clients import DataTestClient


class GoodsVerifiedTests(DataTestClient):

    def setUp(self):
        super().setUp()

        self.report_summary = self.create_picklist_item('Report Summary',
                                                        self.team,
                                                        PicklistType.REPORT_SUMMARY,
                                                        PickListStatus.ACTIVE)
        self.good_1 = self.create_controlled_good('this is a good', self.organisation)
        # self.good_2 = self.create_controlled_good('this is a good as well', self.organisation)
        self.url = reverse('goods:control_code')

    def test_verify_single_good(self):
        data = {
            'objects': self.good_1.pk,
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': 'ML1a',
            'is_good_controlled': True,
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_verify_single_good_in_array(self):
        data = {
            'good': [self.good_1.pk],
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': 'ML1a',
            'is_good_controlled': True,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_verify_multiple_goods(self):
        data = {
            'good': [self.good_1.pk, self.good_2.pk],
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': 'ML1a',
            'is_good_controlled': True,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
