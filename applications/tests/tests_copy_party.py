from django.urls import reverse
from rest_framework import status

from applications.models import PartyOnApplication
from parties.models import Party
from test_helpers.clients import DataTestClient


class CopyPartyTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application(self.organisation)

    def test_copy_party(self):
        """
        Given a standard draft has been created
        And the draft does not yet contain a consignee
        When a new consignee is added
        Then the consignee is successfully added to the draft
        """
        party = PartyOnApplication.objects.filter(application=self.draft).first().party
        url = reverse("applications:copy_party", kwargs={"pk": self.draft.id, "party_pk": party.id})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["party"], Party.objects.copy_detail(pk=party.id))
