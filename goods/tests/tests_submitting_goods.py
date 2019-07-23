from django.urls import reverse
from rest_framework import status

from drafts.models import GoodOnDraft
from goods.models import Good
from static.units.enums import Units
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class GoodTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.org = self.test_helper.organisation
        self.draft = OrgAndUserHelper.complete_draft('Goods test', self.org)

    def test_submitted_good_changes_status(self):
        """
        Test that the good's status is set to submitted
        """
        draft = self.test_helper.create_draft_with_good_end_user_and_site('test', self.org)
        self.assertEqual(Good.objects.get().status, 'draft')
        self.test_helper.submit_draft(self, draft=draft)
        self.assertEqual(Good.objects.get().status, 'submitted')

    def test_submitted_good_cannot_be_edited(self):
        """
        Tests that the good cannot be edited after submission
        """
        draft = self.test_helper.create_draft_with_good_end_user_and_site('test', self.org)
        self.test_helper.submit_draft(self, draft=draft)
        good = Good.objects.get()
        url = reverse('goods:good', kwargs={'pk': good.id})
        data = {}
        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsubmitted_good_can_be_edited(self):
        """
        Tests that the good can be edited after submission
        """
        self.test_helper.create_draft_with_good_end_user_and_site('test', self.org)
        good = Good.objects.get()
        url = reverse('goods:good', kwargs={'pk': good.id})
        data = {'description': 'some great good'}
        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Good.objects.get().description, 'some great good')

    def test_submitted_good_cannot_be_deleted(self):
        """
        Tests that the good cannot be deleted after submission
        """
        draft = self.test_helper.create_draft_with_good_end_user_and_site('test', self.org)
        self.test_helper.submit_draft(self, draft=draft)
        good = Good.objects.get()
        url = reverse('goods:good', kwargs={'pk': good.id})
        response = self.client.delete(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Good.objects.count(), 1)

    def test_unsubmitted_good_can_be_deleted(self):
        """
        Tests that the good can be deleted after submission
        """
        self.test_helper.create_draft_with_good_end_user_and_site('test', self.org)
        good = Good.objects.get()
        url = reverse('goods:good', kwargs={'pk': good.id})
        response = self.client.delete(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Good.objects.count(), 0)

    def test_deleted_good_removed_from_all_drafts_they_existed_in(self):
        """
        Tests that goods get deleted from drafts that they were assigned to, after good deletion
        """
        self.test_helper.create_draft_with_good_end_user_and_site('testOne', self.org)
        draft_two = self.test_helper.complete_draft('testTwo', self.org)
        good = Good.objects.get()
        GoodOnDraft(good=good, draft=draft_two, quantity=10, unit=Units.NAR, value=500).save()
        self.assertEqual(Good.objects.all().count(), 1)
        self.assertEqual(GoodOnDraft.objects.count(), 2)
        url = reverse('goods:good', kwargs={'pk': good.id})
        response = self.client.delete(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Good.objects.all().count(), 0)
        self.assertEqual(GoodOnDraft.objects.count(), 0)
