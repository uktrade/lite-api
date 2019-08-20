# from django.urls import reverse
# from rest_framework import status
#
# from test_helpers.clients import DataTestClient
# from test_helpers.helpers import create_additional_users
# from users.enums import UserStatuses


# class UserTests(DataTestClient):

    # def test_deactivate_a_user(self):
    #     user = create_additional_users(self.organisation)
    #
    #     data = {
    #         'status': UserStatuses.DEACTIVATED
    #     }
    #
    #     url = reverse('users:user', kwargs={'pk': user.id})
    #     response = self.client.put(url, data, **self.exporter_headers)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #
    # def test_cannot_deactivate_self(self):
    #     data = {
    #         'status': UserStatuses.DEACTIVATED
    #     }
    #
    #     url = reverse('users:user', kwargs={'pk': self.exporter_user.id})
    #     response = self.client.put(url, data, **self.exporter_headers)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_deactivate_and_reactivate_a_user(self):
    #     user = create_additional_users(self.organisation)
    #     url = reverse('users:authenticate')
    #
    #     data = {
    #         'email': user.email,
    #         'first_name': user.first_name,
    #         'last_name': user.last_name
    #     }
    #
    #     response = self.client.post(url, data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     data = {
    #         'status': UserStatuses.DEACTIVATED
    #     }
    #     url = reverse('users:user', kwargs={'pk': user.id})
    #     self.client.put(url, data, **self.exporter_headers)
    #     data = {
    #         'status': UserStatuses.ACTIVE
    #     }
    #     self.client.put(url, data, **self.exporter_headers)
    #     url = reverse('users:authenticate')
    #     data = {
    #         'email': user.email,
    #         'first_name': user.first_name,
    #         'last_name': user.last_name
    #     }
    #     response = self.client.post(url, data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
