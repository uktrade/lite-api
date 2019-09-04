# from parameterized import parameterized
# from rest_framework import status
# from rest_framework.reverse import reverse
#
# from test_helpers.clients import DataTestClient
#
#
# class EUAETests(DataTestClient):
#
#     def setUp(self):
#         super().setUp()
#         self.url = reverse('end-users:EUAE-query')
#         self.organisation = self.create_organisation('TAT')
#         self.end_user = self.create_end_user('endUser', self.organisation)
#         self.end_user_fail = {'id': 0000000000}
#
#
#     @parameterized.expand([
#         (True, 'These are details', 'Because I\'m unsure', status.HTTP_201_CREATED),  # Create a new EUAE query
#         (True, '', 'Because I\'m unsure', status.HTTP_201_CREATED),
#         (True, 'These are details', '', status.HTTP_201_CREATED),
#         (False, 'These are details', 'Because I\'m unsure', status.HTTP_404_NOT_FOUND),
#         (False, '', '', status.HTTP_404_NOT_FOUND),
#     ])
#     def test_create_EUAE_query(self, real_end_user, details, raised_reason, expected_status):
#         if real_end_user:
#             end_user = self.end_user.id
#         else:
#             end_user = self.end_user_fail['id']
#
#         data = {
#             'end_user_id': end_user,
#             'details': details,
#             'raised_reason': raised_reason
#         }
#         response = self.client.post(self.url, data, **self.exporter_headers)
#
#         self.assertEquals(response.status_code, expected_status)
#
#         if response.status_code == status.HTTP_201_CREATED:
#             response_data = response.json()
#             self.assertIn('id', response_data)
#
