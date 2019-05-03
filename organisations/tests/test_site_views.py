
from django.urls import path, include
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from test_helpers.org_and_user_helper import OrgAndUserHelper


class SiteViewTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    # def setUp(self):
    #     self.test_helper = OrgAndUserHelper(name='name')
    #     self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}
    #
    # def test_site_list(self):
    #     url = reverse('organisations:sites', )
    #     response = self.client.get(url, **self.headers)



