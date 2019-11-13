from django.urls import reverse_lazy
from rest_framework import status

from applications.models import GoodOnApplication
from cases.models import Case
from conf.constants import Permissions
from goods.models import Good
from picklists.enums import PicklistType, PickListStatus
from static.units.enums import Units
from test_helpers.clients import DataTestClient
from users.models import Role, GovUser


class GoodsVerifiedTests(DataTestClient):

    def setUp(self):
        super().setUp()

        self.report_summary = self.create_picklist_item('Report Summary',
                                                        self.team,
                                                        PicklistType.REPORT_SUMMARY,
                                                        PickListStatus.ACTIVE)

        self.good_1 = self.create_controlled_good('this is a good', self.organisation)
        self.good_1.flags.set([self.create_flag('New Flag', 'Good', self.team)])
        self.good_2 = self.create_controlled_good('this is a good as well', self.organisation)

        role = Role(name='review_goods')
        role.permissions.set([Permissions.REVIEW_GOODS])
        role.save()
        self.gov_user.role = role
        self.gov_user.save()

        self.draft = self.create_standard_application(organisation=self.organisation)
        GoodOnApplication(good=self.good_1,
                          application=self.draft,
                          quantity=10,
                          unit=Units.NAR,
                          value=500).save()
        GoodOnApplication(good=self.good_2,
                          application=self.draft,
                          quantity=10,
                          unit=Units.NAR,
                          value=500).save()
        self.submit_application(self.draft)
        self.case = Case.objects.get(application=self.draft)
        self.url = reverse_lazy('goods:control_code', kwargs={'case_pk': self.case.id})

    def test_verify_single_good(self):
        data = {
            'objects': self.good_1.pk,
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': 'ML1a',
            'is_good_controlled': 'yes',
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertEqual(verified_good.control_code, 'ML1a')

        # determine that flags have been removed when good verified
        self.assertEqual(verified_good.flags.count(), 0)

    def test_verify_multiple_goods(self):
        data = {
            'objects': [self.good_1.pk, self.good_2.pk],
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': 'ML1a',
            'is_good_controlled': 'yes',
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertEqual(verified_good.control_code, 'ML1a')

        verified_good = Good.objects.get(pk=self.good_2.pk)
        self.assertEqual(verified_good.control_code, 'ML1a')

    def test_verify_single_good_NLR(self):
        data = {
            'objects': self.good_1.pk,
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': 'ML1a',
            'is_good_controlled': 'no',
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertEqual(verified_good.control_code, '')

        # determine that flags have been removed when good verified
        self.assertEqual(verified_good.flags.count(), 0)

    def test_verify_multiple_goods_NLR(self):
        data = {
            'objects': [self.good_1.pk, self.good_2.pk],
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': '',
            'is_good_controlled': 'no',
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertEqual(verified_good.control_code, '')

        verified_good = Good.objects.get(pk=self.good_2.pk)
        self.assertEqual(verified_good.control_code, '')

    def test_invalid_pk(self):
        data = {
            'objects': [self.team.pk, self.good_1.pk],  # first value is invalid
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': '',
            'is_good_controlled': 'no',
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertEqual(verified_good.control_code, '')

    def test_invalid_control_code(self):
        data = {
            'objects': [self.good_1.pk, self.good_2.pk],
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': 'invalid',
            'is_good_controlled': 'yes',
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

        # since it has an invalid control code, flags should not be removed
        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertEqual(verified_good.flags.count(), 1)

    def test_controlled_good_empty_control_code(self):
        data = {
            'objects': [self.good_1.pk, self.good_2.pk],
            'comment': 'I Am Easy to Find',
            'report_summary': self.report_summary.pk,
            'control_code': '',
            'is_good_controlled': 'yes',
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

        # since it has an empty control code, flags should not be removed
        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertEqual(verified_good.flags.count(), 1)

    def test_user_cannot_respond_to_good_without_permissions(self):
        """
        Tests that the right level of permissions are required
        """
        # create a second user to adopt the super user role as it will
        # overwritten otherwise if we try and remove the role from the first
        valid_user = GovUser(email='test2@mail.com', first_name='John', last_name='Smith', team=self.team, role=self.super_user_role)
        valid_user.save()

        self.gov_user.role = self.default_role
        self.gov_user.save()

        response = self.client.post(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
