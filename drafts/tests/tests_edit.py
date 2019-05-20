from rest_framework import status
from rest_framework.reverse import reverse

from drafts.models import Draft
from test_helpers.clients import DataTestClient


class DraftTests(DataTestClient):

    def test_edit_draft(self):
        """
        Ensure we can edit a draft object.
        """
        draft = self.test_helper.complete_draft('Draft', self.test_helper.organisation)

        url = reverse('drafts:draft', kwargs={'pk': draft.id})
        data = {'destination': 'France'}
        response = self.client.put(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().id, draft.id)
        self.assertEqual(Draft.objects.get().destination, 'France')
