from rest_framework import status
from django.test import TestCase
from drafts.models import Draft


class DraftTests(TestCase):

    # Creation

    def test_create_draft(self):
        """
            Ensure we can create a new draft object.
            """
        url = '/drafts/'
        data = {'user_id': '12345'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().user_id, '12345')

    def test_create_draft_empty_user_id(self):
        """
            Ensure we cannot create a draft with an empty user_id.
            """
        url = '/drafts/'
        data = {'user_id': ''}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(Draft.objects.count(), 0)

    def test_create_draft_no_user_id(self):
        """
            Ensure we cannot create a draft without a user_id.
            """
        url = '/drafts/'
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(Draft.objects.count(), 0)

    # Editing

    def test_edit_draft(self):
        """
            Ensure we can edit a draft object.
            """
        control_code = 'ML1a'

        draft = Draft(user_id="12345")
        draft.save()

        url = '/drafts/' + str(draft.id) + '/'
        data = {'control_code': control_code}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().id, draft.id)
        self.assertEqual(Draft.objects.get().control_code, control_code)

    # Viewing

    def test_view_drafts(self):
        """
            Ensure we can get a list of drafts.
            """
        complete_draft = Draft(user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")
        complete_draft.save()

        url = '/drafts/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_draft(self):
        """
            Ensure we can get a draft.
            """
        complete_draft = Draft(user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")
        complete_draft.save()

        url = '/drafts/' + str(complete_draft.id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_incorrect_draft(self):
        """
            Ensure we cannot get a draft if the id is incorrect.
            """
        complete_draft = Draft(user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")
        complete_draft.save()

        url = '/drafts/invalid_id/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
