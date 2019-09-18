from django.urls import reverse
from rest_framework import status

from applications.models import Application, GoodOnApplication
from drafts.models import GoodOnDraft, SiteOnDraft
from static.units.enums import Units
from test_helpers.clients import DataTestClient


class ApplicationsTests(DataTestClient):

    url = reverse('applications:applications')

    def test_that_goods_are_added_to_application_when_submitted(self):
        draft = self.create_draft(self.organisation)
        good = self.create_controlled_good('test good', self.organisation)
        SiteOnDraft(site=self.organisation.primary_site, draft=draft).save()

        GoodOnDraft(draft=draft, good=good, quantity=20, unit=Units.NAR, value=400).save()
        GoodOnDraft(draft=draft, good=good, quantity=90, unit=Units.KGM, value=500).save()
        draft.end_user = self.create_end_user('test', self.organisation)
        draft.consignee = self.create_consignee('test', self.organisation)
        self.create_document_for_party(draft.end_user)
        self.create_document_for_party(draft.consignee)
        draft.save()

        data = {
            'id': draft.id
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GoodOnApplication.objects.count(), 2)
        application = Application.objects.get()
        self.assertEqual(GoodOnApplication.objects.filter(application=application).count(), 2)

    def test_that_cannot_submit_with_no_goods(self):
        draft = self.create_draft(self.organisation)
        draft.end_user = self.create_end_user("End user", self.organisation)
        draft.save()

        self.create_document_for_party(draft.end_user)

        site_on_draft_1 = SiteOnDraft(site=self.organisation.primary_site, draft=draft)
        site_on_draft_1.save()

        url = reverse('applications:applications')
        data = {'id': draft.id}
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
