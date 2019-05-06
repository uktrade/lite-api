from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from applications.models import Application
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ApplicationsTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_update_status_of_an_application(self):
        application = Application(id='90d6c724-0339-425a-99d2-9d2b8e864ec7',
                                  name='Test',
                                  destination='Poland',
                                  activity='Trade',
                                  usage='Trade')
        application.save()
        url = reverse('applications:application', kwargs={'pk': application.id})
        data = {'id': application.id, 'status': 'withdrawn'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Application.objects.get(pk=application.id).status.name, "withdrawn")
