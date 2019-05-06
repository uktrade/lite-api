import json
from uuid import UUID

from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from drafts.models import Draft
from test_helpers.org_and_user_helper import OrgAndUserHelper


class DraftTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_view_drafts(self):
        """
            Ensure we can get a list of drafts.
        """
        OrgAndUserHelper.complete_draft(name='test 1', org=self.test_helper.organisation).save()
        OrgAndUserHelper.complete_draft(name='test 2', org=self.test_helper.organisation).save()

        url = reverse('drafts:drafts')
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['drafts']), 2)

    def test_view_drafts_not_applications(self):
        """
            Ensure that when a draft is submitted it does not get submitted as an application
        """
        draft = OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)

        url = reverse('applications:application', kwargs={'pk': draft.id})
        response = self.client.get(url, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_draft(self):
        """
            Ensure we can get a draft.
        """
        draft = OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)

        url = reverse('drafts:draft', kwargs={'pk': draft.id})
        response = self.client.get(url, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_incorrect_draft(self):
        """
            Ensure we cannot get a draft if the id is incorrect.
        """
        OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)
        invalid_id = UUID('90D6C724-0339-425A-99D2-9D2B8E864EC6')

        url = reverse('drafts:draft', kwargs={'pk': invalid_id})
        response = self.client.put(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_only_sees_their_organisations_drafts_in_list(self):
        draft_test_helper_2 = OrgAndUserHelper(name='organisation2')

        draft = OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)
        OrgAndUserHelper.complete_draft(name='test', org=draft_test_helper_2.organisation)

        url = reverse('drafts:drafts')
        response = self.client.get(url, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Draft.objects.count(), 2)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["drafts"]), 1)
        self.assertEqual(response_data["drafts"][0]["organisation"], str(draft.organisation.id))

    def test_user_cannot_see_details_of_another_organisations_draft(self):
        draft_test_helper_2 = OrgAndUserHelper(name='organisation2')
        draft = OrgAndUserHelper.complete_draft(name='test', org=draft_test_helper_2.organisation)

        url = reverse('drafts:draft', kwargs={'pk': draft.id})

        response = self.client.get(url, **{'HTTP_USER_ID': str(self.test_helper.user.id)})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
