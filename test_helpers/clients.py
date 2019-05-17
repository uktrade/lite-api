from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient
from conf.urls import urlpatterns
from test_helpers.org_and_user_helper import OrgAndUserHelper


class BaseTestClient(APITestCase, URLPatternsTestCase):
    """
    Base test client which provides only URL patterns and client
    """
    urlpatterns = urlpatterns
    client = APIClient


class DataTestClient(BaseTestClient):
    """
    Test client which creates an initial organisation and user
    """
    def setUp(self):
        super().setUp()
        self.test_helper = OrgAndUserHelper(name='Org1')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}
