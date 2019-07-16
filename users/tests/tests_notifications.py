import json

from django.urls import path, include, reverse
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from cases.models import Case
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper
from users.models import User, Notification


class NotificationTests(DataTestClient):

    urlpatterns = [
        path('users/', include('users.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def setUp(self):
        super().setUp()

    def tests_create_new_clc_query_notification(self):

        self.create_clc_query_case("Case Ref")
        self.assertEqual(Case.objects.all().count(), 1)
        # note = self.create_case_note(self.case, "This is a test note")
        # Notification(user=self.user, note=note, viewed_at=None)
        # self.assertEqual(Notification.objects.all().count(), 1)

    # def tests_create_new_application_notification(self):
    #     case = self.create_clc_query_case("Case Ref")
    #     note = self.create_case_note(case, "This is a test note")
    #     Notification(user=self.user, note=note, viewed_at=None)
    #     self.assertEqual(Notification.all().count(), 1)