import json

from django.urls import reverse

from gov_users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper
from users.models import ExporterUser


class UserTests(DataTestClient):

    def test_only_get_users_belonging_to_my_organisation(self):
        test_helper_2 = OrgAndUserHelper(name='banana')
        organisation_2 = test_helper_2.organisation
        organisation_1 = self.test_helper.organisation

        OrgAndUserHelper.create_additional_users(organisation_1, 2)
        OrgAndUserHelper.create_additional_users(organisation_2, 4)

        self.assertEqual(ExporterUser.objects.all().count(), 8)
        url = reverse('users:users')
        response = self.client.get(url, **self.exporter_headers)
        response_data = json.loads(response.content)
        # Expect to see one more than the additional number of users created as there is one initial admin user
        self.assertEqual(len(response_data["users"]), 3)

        response = self.client.get(url, **{'HTTP_EXPORTER_USER_TOKEN': user_to_token(test_helper_2.user)})
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["users"]), 5)
