from django.urls import reverse
from rest_framework import status

from applications.models import Application
from content_strings.strings import get_string
from drafts.models import GoodOnDraft
from goods.models import Good
from test_helpers.clients import DataTestClient


class ApplicationUltimateEndUserTests(DataTestClient):
    url = reverse('applications:applications')

    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)

        part_good = Good(is_good_end_product=False,
                         is_good_controlled=True,
                         control_code='ML17',
                         organisation=self.organisation,
                         description='a good',
                         part_number='123456')
        part_good.save()

        GoodOnDraft(good=part_good,
                    draft=self.draft,
                    quantity=17,
                    value=18).save()

        self.end_user = self.create_end_user('ultimate end user', self.organisation)

    def test_submit_draft_with_ultimate_end_users_success(self):
        ultimate_end_user = self.create_ultimate_end_user("Ultimate End user", self.organisation)
        self.draft.ultimate_end_users.add(ultimate_end_user)
        self.create_document_for_party(party=ultimate_end_user,
                                       name='file343.pdf',
                                       safe=True)

        data = {'id': self.draft.id}
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Application.objects.get().ultimate_end_users.first(), ultimate_end_user)

    def test_submit_draft_with_no_ultimate_end_users_unsuccessful(self):
        """
        This should be unsuccessful as an ultimate end user is required when
        there is a part which is to be incorporated into another good
        """
        data = {'id': self.draft.id}
        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data, {
            'errors': {'ultimate_end_users': get_string('applications.standard.no_ultimate_end_users_set')}})
