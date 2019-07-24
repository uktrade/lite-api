import json
from uuid import UUID

from django.urls import reverse
from rest_framework import status

from drafts.models import Draft
from gov_users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class DraftTests(DataTestClient):
    def test_view_drafts(self):
        """
        Ensure we can get a list of drafts.
        """
        OrgAndUserHelper.complete_draft(name='test 1', org=self.test_helper.organisation).save()
        OrgAndUserHelper.complete_draft(name='test 2', org=self.test_helper.organisation).save()

        url = reverse('drafts:drafts')
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['drafts']), 2)

    def test_view_draft(self):
        """
        Ensure we can get a draft.
        """
        draft = OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)

        url = reverse('drafts:draft', kwargs={'pk': draft.id})
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_incorrect_draft(self):
        """
        Ensure we cannot get a draft if the id is incorrect.
        """
        OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)
        invalid_id = UUID('90D6C724-0339-425A-99D2-9D2B8E864EC6')

        url = reverse('drafts:draft', kwargs={'pk': invalid_id})
        response = self.client.put(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_only_sees_their_organisations_drafts_in_list(self):
        draft_test_helper_2 = OrgAndUserHelper(name='organisation2')

        draft = OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)
        OrgAndUserHelper.complete_draft(name='test', org=draft_test_helper_2.organisation)

        url = reverse('drafts:drafts')
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Draft.objects.count(), 2)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["drafts"]), 1)
        self.assertEqual(response_data["drafts"][0]["organisation"], str(draft.organisation.id))

    def test_user_cannot_see_details_of_another_organisations_draft(self):
        draft_test_helper_2 = OrgAndUserHelper(name='organisation2')
        draft = OrgAndUserHelper.complete_draft(name='test', org=draft_test_helper_2.organisation)

        url = reverse('drafts:draft', kwargs={'pk': draft.id})

        response = self.client.get(url, **{'HTTP_EXPORTER_USER_TOKEN': user_to_token(self.test_helper.user)})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
