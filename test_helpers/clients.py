from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient
from conf.urls import urlpatterns
from test_helpers.org_and_user_helper import OrgAndUserHelper


class BaseTestClient(APITestCase, URLPatternsTestCase):
    urlpatterns = urlpatterns
    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='Org1')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}
