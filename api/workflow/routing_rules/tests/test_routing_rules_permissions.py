from django.urls import reverse
from rest_framework import status

from api.conf import constants
from api.static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from api.users.models import Role


class RoutingRuleCreationTests(DataTestClient):
    def setUp(self):
        super(RoutingRuleCreationTests, self).setUp()

        self.routing_rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.last().id,
            additional_rules=[],
        )

        self.url = reverse("routing_rules:detail", kwargs={"pk": self.routing_rule.id})

    def test_all_permissions_works(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manage_all_permission_works_for_own_team_rules(self):
        role = Role.objects.create(name="test")
        role.permissions.set([constants.GovPermissions.MANAGE_ALL_ROUTING_RULES.name])
        self.gov_user.role = role
        self.gov_user.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manage_team_permission_works_for_own_team_rules(self):
        role = Role.objects.create(name="test")
        role.permissions.set([constants.GovPermissions.MANAGE_TEAM_ROUTING_RULES.name])
        self.gov_user.role = role
        self.gov_user.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manage_all_permission_works_for_other_team_rules(self):
        role = Role.objects.create(name="test")
        role.permissions.set([constants.GovPermissions.MANAGE_ALL_ROUTING_RULES.name])
        other_team = self.create_team("other")
        self.gov_user.role = role
        self.gov_user.team = other_team
        self.gov_user.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manage_team_permission_fails_for_other_team_rules(self):
        role = Role.objects.create(name="test")
        role.permissions.set([constants.GovPermissions.MANAGE_TEAM_ROUTING_RULES.name])
        other_team = self.create_team("other")
        self.gov_user.role = role
        self.gov_user.team = other_team
        self.gov_user.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_permission_fails(self):
        role = Role.objects.create(name="test")
        self.gov_user.role = role
        self.gov_user.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
