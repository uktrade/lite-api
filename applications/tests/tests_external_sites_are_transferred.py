from django.urls import reverse
from rest_framework import status

from applications.models import BaseApplication, ExternalLocationOnApplication, SiteOnApplication, GoodOnApplication
from static.units.enums import Units
from test_helpers.clients import DataTestClient


class ApplicationsTests(DataTestClient):

    def test_that_external_locations_are_added_to_application_when_submitted(self):
        draft = self.create_standard_draft(self.organisation)
        site1 = self.create_external_location('site1', self.organisation)
        site2 = self.create_external_location('site2', self.organisation)
        unit1 = Units.NAR
        good = self.create_controlled_good('test good', self.organisation)
        GoodOnApplication(application=draft, good=good, quantity=20, unit=unit1, value=400).save()
        ExternalLocationOnApplication(external_location=site1, draft=draft).save()
        ExternalLocationOnApplication(external_location=site2, draft=draft).save()
        draft.end_user = self.create_end_user('test', self.organisation)
        draft.consignee = self.create_consignee('test', self.organisation)
        self.create_document_for_party(draft.end_user)
        self.create_document_for_party(draft.consignee)
        draft.activity = 'Brokering'
        draft.save()

        url = reverse('applications:applications')
        data = {'id': draft.id}
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExternalLocationOnApplication.objects.count(), 2)
        application = BaseApplication.objects.get()
        self.assertEqual(ExternalLocationOnApplication.objects.filter(application=application).count(), 2)
        self.assertEqual(SiteOnApplication.objects.filter(application=application).count(), 0)
        self.assertEqual(application.activity, 'Brokering')
