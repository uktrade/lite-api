from rest_framework import status
from django.test import TestCase, Client
from drafts.models import Draft


class DraftTests(TestCase):

    # Creation

    def test_create_draft(self):
        """
            Ensure we can create a new draft object.
            """
        url = 'http://localhost:8000/drafts/'
        data = {'user_id': '12345'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().user_id, '12345')

    def test_create_draft_empty_user_id(self):
        """
            Ensure we cannot create a draft with an empty user_id.
            """
        url = 'http://localhost:8000/drafts/'
        data = {'user_id': ''}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(Draft.objects.count(), 0)

    def test_create_draft_no_user_id(self):
        """
            Ensure we cannot create a draft without a user_id.
            """
        url = 'http://localhost:8000/drafts/'
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(Draft.objects.count(), 0)

    # Viewing

    def test_view_drafts(self):
        """
            Ensure we can get a list of drafts.
            """
        complete_draft = Draft(id="90D6C724-0339-425A-99D2-9D2B8E864EC7",
                               user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")
        complete_draft.save()

        url = 'http://localhost:8000/drafts/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
