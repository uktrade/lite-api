from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from conf.urls import urlpatterns
from gov_users.models import GovUser
from static.urls import urlpatterns as static_urlpatterns
from teams.models import Team
from test_helpers.org_and_user_helper import OrgAndUserHelper


class BaseTestClient(APITestCase, URLPatternsTestCase):
    """
    Base test client which provides only URL patterns and client
    """
    urlpatterns = urlpatterns + static_urlpatterns
    client = APIClient


class DataTestClient(BaseTestClient):
    """
    Test client which creates an initial organisation and user
    """
    def setUp(self):
        super().setUp()
        self.test_helper = OrgAndUserHelper(name='Org1')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}
        self.team = Team(name='Admin')
        self.team.save()
        self.user = GovUser(email='test@mail.com',
                            first_name='John',
                            last_name='Smith',
                            team=self.team)
        self.user.save()
        self.gov_headers = {'HTTP_GOV_USER_TOKEN': str(self.user.id)}
