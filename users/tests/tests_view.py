import json

from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from django.urls import path, include, reverse
from test_helpers.org_and_user_helper import OrgAndUserHelper
from users.models import User


class UserTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('users/', include('users.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='apple')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_only_get_users_belonging_to_my_organisation(self):
        test_helper_2 = OrgAndUserHelper(name='banana')
        organisation_2 = test_helper_2.organisation
        organisation_1 = self.test_helper.organisation

        OrgAndUserHelper.create_additional_users(organisation_1, 2)
        OrgAndUserHelper.create_additional_users(organisation_2, 4)

        self.assertEqual(User.objects.all().count(), 8)
        url = reverse('users:users')
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        # Expect to see one more than the additional number of users created as there is one initial admin user
        self.assertEqual(len(response_data["users"]), 3)

        response = self.client.get(url, **{'HTTP_USER_ID': str(test_helper_2.user.id)})
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["users"]), 5)
