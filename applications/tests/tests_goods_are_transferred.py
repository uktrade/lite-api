from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from applications.models import Application, GoodOnApplication
from drafts.models import GoodOnDraft
from test_helpers.org_and_user_helper import OrgAndUserHelper
from quantity.units import Units


class ApplicationsTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_that_goods_are_added_to_application_when_submitted(self):
        draft = OrgAndUserHelper.complete_draft('test', self.test_helper.organisation)
        unit = Units.NAR
        good = OrgAndUserHelper.create_controlled_good('test good', self.test_helper.organisation)
        good_on_draft_1 = GoodOnDraft(draft=draft, good=good, quantity=20, unit=unit, value=400)
        good_on_draft_2 = GoodOnDraft(draft=draft, good=good, quantity=90, unit=unit, value=500)
        good_on_draft_1.save()
        good_on_draft_2.save()

        url = reverse('applications:applications')
        data = {'id': draft.id}
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GoodOnApplication.objects.count(), 2)
        application = Application.objects.get()
        self.assertEqual(GoodOnApplication.objects.filter(application=application).count(), 2)
