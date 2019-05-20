from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from applications.models import Application
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ApplicationsTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('applications/', include('applications.urls')),
    ]

    client = APIClient()

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def given_empty_application_data_when_trying_to_create_application_request_returns_404(self):
        """
            Ensure we cannot create a new application object without a draft id.
        """
        application_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'
        application = Application(id=application_id,
                                  name='Test',
                                  destination='Poland',
                                  activity='Trade',
                                  usage='Fun')
        application.save()

        request_data = {}

        url = reverse('applications:applications')
        response = self.client.post(url, request_data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(Application.objects.filter(id=application_id)), 1)
