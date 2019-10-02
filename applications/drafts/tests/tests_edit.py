# from rest_framework import status
# from rest_framework.reverse import reverse
#
# from applications.models import StandardApplication
# from test_helpers.clients import DataTestClient
#
#
# class DraftTests(DataTestClient):
#
#     TODO: Add edit application/draft functionality
#     def test_edit_draft(self):
#         """
#         Ensure we can edit a draft object.
#         """
#         draft = self.create_standard_draft(self.organisation)
#         url = reverse('drafts:draft', kwargs={'pk': draft.id})
#
#         data = {'name': 'Test'}
#
#         response = self.client.put(url, data, **self.exporter_headers)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         self.assertEqual(StandardApplication.objects.count(), 1)
#         self.assertEqual(StandardApplication.objects.get().id, draft.id)
#         self.assertEqual(StandardApplication.objects.get().name, data['name'])
#
