from django.urls import reverse
from rest_framework import status

from applications.models import Application, GoodOnApplication
from drafts.models import GoodOnDraft
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper
from static.quantity.units import Units


class ApplicationsTests(DataTestClient):

    url = reverse('applications:applications')

    def test_that_goods_are_added_to_application_when_submitted(self):
        draft = OrgAndUserHelper.complete_draft('test', self.test_helper.organisation)
        good = OrgAndUserHelper.create_controlled_good('test good', self.test_helper.organisation)

        GoodOnDraft(draft=draft, good=good, quantity=20, unit=Units.NAR, value=400).save()
        GoodOnDraft(draft=draft, good=good, quantity=90, unit=Units.KGM, value=500).save()

        data = {'id': draft.id}
        response = self.client.post(self.url, data,**self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GoodOnApplication.objects.count(), 2)
        application = Application.objects.get()
        self.assertEqual(GoodOnApplication.objects.filter(application=application).count(), 2)
