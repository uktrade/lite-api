from datetime import datetime

from django.test import tag
from django.urls import reverse
from rest_framework import status

from cases.models import Case
from goods.enums import GoodControlled, GoodStatus
from goods.models import Good
from picklists.enums import PicklistType, PickListStatus
from queries.control_list_classifications.models import ControlListClassificationQuery
from test_helpers.clients import DataTestClient


class ControlListClassificationsQueryCreateTests(DataTestClient):

    url = reverse('queries:control_list_classifications:control_list_classifications')

    def test_create_control_list_classification_query(self):
        """
        Ensure that an exporter can raise a control list
        classification query and that a case has been created
        """
        good = Good(description='Good description',
                    is_good_controlled=GoodControlled.UNSURE,
                    control_code='ML1',
                    is_good_end_product=True,
                    part_number='123456',
                    organisation=self.organisation)
        good.save()

        data = {
            'good_id': good.id,
            'not_sure_details_control_code': 'ML1a',
            'not_sure_details_details': 'I don\'t know',
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data['id'], ControlListClassificationQuery.objects.get().id)
        self.assertEqual(Case.objects.count(), 1)


class ControlListClassificationsQueryUpdateTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.report_summary = self.create_picklist_item('Report Summary',
                                                        self.team,
                                                        PicklistType.ANNUAL_REPORT_SUMMARY,
                                                        PickListStatus.ACTIVE)

        self.query = self.create_clc_query('This is a widget', self.organisation)

        self.url = reverse('queries:control_list_classifications:control_list_classification',
                           kwargs={'pk': self.query.pk})

    def test_respond_to_control_list_classification_query(self):
        """
        Ensure that a gov user can respond to a control list
        classification query with a control code
        """
        data = {
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': 'ML1a',
            'is_good_controlled': True,
        }

        response = self.client.put(self.url, data, **self.gov_headers)
        self.query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.query.comment, data['comment'])
        self.assertEqual(self.query.report_summary, self.report_summary.text)
        self.assertEqual(self.query.good.control_code, data['control_code'])
        self.assertEqual(self.query.good.is_good_controlled, str(data['is_good_controlled']))
        self.assertEqual(self.query.good.status, GoodStatus.FINAL)

    def test_respond_to_control_list_classification_query_nlr(self):
        """
        Ensure that a gov user can respond to a control list
        classification query with no licence required
        """
        data = {
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'is_good_controlled': False,
        }

        response = self.client.put(self.url, data, **self.gov_headers)
        self.query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.query.comment, data['comment'])
        self.assertEqual(self.query.report_summary, self.report_summary.text)
        self.assertEqual(self.query.good.control_code, '')
        self.assertEqual(self.query.good.is_good_controlled, str(data['is_good_controlled']))
        self.assertEqual(self.query.good.status, GoodStatus.FINAL)

    def test_respond_to_control_list_classification_query_failure(self):
        """
        Ensure that a gov user cannot respond to a control list
        classification query without providing data
        """
        data = {}

        response = self.client.put(self.url, data, **self.gov_headers)
        self.query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.query.good.status, GoodStatus.DRAFT)
