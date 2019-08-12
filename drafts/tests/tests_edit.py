from rest_framework import status
from rest_framework.reverse import reverse

from drafts.models import Draft
from test_helpers.clients import DataTestClient


class DraftTests(DataTestClient):

    def test_edit_draft(self):
        """
        Ensure we can edit a draft object.
        """
        draft = self.create_draft(self.exporter_user.organisation)
        url = reverse('drafts:draft', kwargs={'pk': draft.id})

        data = {'name': 'Test'}

        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().id, draft.id)
        self.assertEqual(Draft.objects.get().name, data['name'])
