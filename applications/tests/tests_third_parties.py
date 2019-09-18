from django.urls import reverse
from rest_framework import status

from applications.models import Application
from drafts.models import GoodOnDraft
from goods.models import Good
from test_helpers.clients import DataTestClient


class ApplicationThirdPartyTests(DataTestClient):
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

        self.end_user = self.create_end_user('end user', self.organisation)

    def test_submit_draft_with_third_party_success(self):
        """
        Given a standard draft has been created with a third party
        When the third party is submitted
        Then the draft is converted to an application
        """

        ultimate_end_user = self.create_ultimate_end_user("Third party", self.organisation)
        self.draft.ultimate_end_users.add(ultimate_end_user)
        self.create_document_for_party(party=ultimate_end_user,
                                       name='file343.pdf',
                                       safe=True)

        third_party = self.create_third_party("Third party", self.organisation)
        self.draft.third_parties.add(third_party)

        data = {'id': self.draft.id}
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Application.objects.get().third_parties.first(), third_party)
