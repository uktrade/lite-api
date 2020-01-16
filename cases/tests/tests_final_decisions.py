from django.urls import reverse
from rest_framework import status

from conf.constants import GovPermissions
from test_helpers.clients import DataTestClient
from users.models import Role


class CaseFinalDecisionTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.url = reverse("cases:activity", kwargs={"pk": self.case.id})

    def test_cannot_make_final_decision_without_permission(self):
        self.gov_user.role = self.default_role
        self.gov_user.save()

        data = {"duration": 10}

        response = self.client.put(
            reverse("applications:finalise", kwargs={"pk": self.standard_application.id}),
            data=data,
            **self.gov_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_record_final_decision_with_correct_permissions(self):
        role = Role(name="some")
        role.permissions.set([GovPermissions.MANAGE_FINAL_ADVICE.name, GovPermissions.MANAGE_LICENCE_DURATION.name])
        role.save()
        self.gov_user.role = role
        self.gov_user.save()

        data = {"duration": 10}

        response = self.client.put(
            reverse("applications:finalise", kwargs={"pk": self.standard_application.id}),
            data=data,
            **self.gov_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
