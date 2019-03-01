from rest_framework import status
from django.test import TestCase, Client
from drafts.models import Draft
from applications.models import Application


class ApplicationTests(TestCase):

    # Creation

    def test_create_application(self):
        """
            Ensure we can create a new draft object.
            """
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        complete_draft = Draft(id=draft_id,
                               user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")
        complete_draft.save()

        url = '/applications/'
        data = {'id': draft_id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(Draft.objects.filter(id=draft_id)), 0)
        self.assertEqual(Application.objects.get(id=draft_id).destination, "Poland")

    def test_create_application_with_invalid_id(self):
        """
            Ensure we cannot create a new application object with an invalid draft id.
            """
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        complete_draft = Draft(id=draft_id,
                               user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")
        complete_draft.save()

        url = '/applications/'
        data = {'id': "90D6C724-0339-425A-99D2-9D2B8E864EC6"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(len(Draft.objects.filter(id=draft_id)), 1)

    def test_create_application_without_id(self):
        """
            Ensure we cannot create a new application object without a draft id.
            """
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        complete_draft = Draft(id=draft_id,
                               user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")
        complete_draft.save()

        url = '/applications/'
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(len(Draft.objects.filter(id=draft_id)), 1)
