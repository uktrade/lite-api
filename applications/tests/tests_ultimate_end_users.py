from django.urls import reverse
from rest_framework import status

from applications.models import Application
from drafts.models import GoodOnDraft
from goods.models import Good
from test_helpers.clients import DataTestClient


class ApplicationUltimateEndUserTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.org = self.test_helper.organisation
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('draft', self.org)
        part_good = Good(is_good_end_product=False,
                         is_good_controlled=True,
                         control_code='ML17',
                         organisation=self.org,
                         description='a good',
                         part_number='123456')
        part_good.save()
        GoodOnDraft(good=part_good,
                    draft=self.draft,
                    quantity=17,
                    value=18).save()
        self.url = reverse('applications:applications')
        self.end_user = self.test_helper.create_end_user('ultimate end user', self.org)

    def test_submit_draft_with_ultimate_end_users_success(self):
        self.draft.ultimate_end_users.add(str(self.end_user.id))

        data = {'id': self.draft.id}
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(str(Application.objects.get().ultimate_end_users.values_list('id', flat=True)[0]), str(self.end_user.id))

    def test_submit_draft_with_no_ultimate_end_users_unsuccessful(self):
        """
        This should be unsuccessful as an ultimate end user is required when
        there is a part which is to be incorporated into another good
        """
        data = {'id': self.draft.id}
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
