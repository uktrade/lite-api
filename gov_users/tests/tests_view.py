from django.urls import path, include, reverse
from rest_framework import status

from gov_users.models import GovUser
from test_helpers.clients import DataTestClient


class GovUserViewTests(DataTestClient):

    urlpatterns = [
        path('gov-users/', include('gov_users.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    def setUp(self):
        super().setUp()
        self.gov_user_preexisting_count = GovUser.objects.all().count()

    def tests_get(self):
        GovUser(email='test2@mail.com',first_name='John',last_name='Smith',team=self.team).save()
        response = self.client.get(reverse('gov_users:gov_users'), **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GovUser.objects.all().count(), self.gov_user_preexisting_count + 1)
