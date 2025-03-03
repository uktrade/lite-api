from django.urls import reverse
from rest_framework import status

from api.addresses.tests.factories import AddressFactoryGB
from api.core.constants import Roles
from api.core.helpers import convert_queryset_to_str, date_to_drf_date
from api.gov_users.enums import GovUserStatuses
from api.organisations.enums import OrganisationStatus, OrganisationType
from api.organisations.tests.factories import OrganisationFactory, SiteFactory
from api.queues.constants import MY_TEAMS_QUEUES_CASES_ID
from api.queues.tests.factories import QueueFactory
from api.users.models import Role
from test_helpers.clients import DataTestClient
from test_helpers.helpers import generate_key_value_pair
from api.users.libraries.get_user import get_user_organisation_relationship
from api.users.models import GovUser
from api.users.tests.factories import GovUserFactory
from parameterized import parameterized


class UserTests(DataTestClient):
    def test_user_can_view_their_own_profile_info(self):
        """
        Tests the 'users/me' endpoint
        Ensures that the endpoint returns the correct details about the signed in user
        """
        response = self.client.get(reverse("users:me"), **self.exporter_headers)
        response_data = response.json()
        relationship = get_user_organisation_relationship(self.exporter_user, self.organisation)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data,
            {
                "id": str(self.exporter_user.pk),
                "first_name": self.exporter_user.first_name,
                "last_name": self.exporter_user.last_name,
                "organisations": [
                    {
                        "id": str(relationship.organisation.id),
                        "joined_at": date_to_drf_date(relationship.created_at),
                        "name": relationship.organisation.name,
                        "status": generate_key_value_pair(relationship.organisation.status, OrganisationStatus.choices),
                    }
                ],
                "role": {
                    "id": str(relationship.role.id),
                    "permissions": convert_queryset_to_str(relationship.role.permissions.values_list("id", flat=True)),
                },
            },
        )

    def test_user_select_organisations_exclude_rejected_orgs(self):
        site_gb = SiteFactory(address=AddressFactoryGB())
        organisation = OrganisationFactory(name="Subsidiary", type=OrganisationType.COMMERCIAL, primary_site=site_gb)
        self.add_exporter_user_to_org(organisation, self.exporter_user)
        response = self.client.get(reverse("users:me"), **self.exporter_headers)
        self.assertEqual(len(response.json()["organisations"]), 2)

        organisation.status = OrganisationStatus.REJECTED
        organisation.save()
        response = self.client.get(reverse("users:me"), **self.exporter_headers)
        active_organisations = response.json()["organisations"]
        self.assertEqual(len(active_organisations), 1)
        self.assertNotIn(organisation.name, [name for name in active_organisations])

    def test_gov_user_list_filtered(self):
        GovUserFactory()
        gov_user = GovUserFactory()
        data = {"email": gov_user.baseuser_ptr.email}
        url = reverse("caseworker_gov_users:list")
        response = self.client.get(url, **self.gov_headers, data=data)
        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["results"][0]["id"] == str(gov_user.pk)
        assert response.json()["results"][0]["email"] == gov_user.email


class UserCaseWorkerTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.gov_user.role = Role.objects.get(id=Roles.INTERNAL_SUPER_USER_ROLE_ID)
        self.gov_user.save()

        self.data = {
            "email": "update@update.me",  # /PS-IGNORE
            "role": str(Roles.INTERNAL_DEFAULT_ROLE_ID),
            "team": str(self.team.id),
            "default_queue": str(MY_TEAMS_QUEUES_CASES_ID),
        }
        self.gov_user_edit = GovUserFactory()
        self.update_url = reverse("caseworker_gov_users:update", kwargs={"pk": self.gov_user_edit.pk})

    def test_gov_user_list_all(self):
        url = reverse("caseworker_gov_users:list")
        response = self.client.get(url, **self.gov_headers, data={})
        assert response.status_code == 200
        assert response.json() == {
            "count": GovUser.objects.count(),
            "total_pages": 1,
            "results": [{"id": str(u.pk), "email": u.email} for u in GovUser.objects.order_by("baseuser_ptr__email")],
        }

    def test_gov_user_list_no_permission(self):
        url = reverse("caseworker_gov_users:list")
        response = self.client.get(url, **self.exporter_headers, data={})
        assert response.status_code == 403

    def test_gov_user_update_sucessfull(self):
        response = self.client.patch(self.update_url, **self.gov_headers, data=self.data)
        assert response.status_code == 200

        gov_user_response = response.json()
        self.gov_user_edit.refresh_from_db()

        for key, value in self.data.items():
            assert gov_user_response[key] == value

    def test_gov_user_update_queue_non_exist(self):
        self.data["default_queue"] = "35cf631f-bf84-43ce-b029-e3f51ba43349"  # /PS-IGNORE

        response = self.client.patch(self.update_url, **self.gov_headers, data=self.data)

        assert response.status_code == 400
        assert response.json()["errors"] == {"default_queue": ["select a valid queue"]}

    def test_gov_user_update_queue_incorrect_team(self):
        self.data["default_queue"] = str(QueueFactory().id)

        response = self.client.patch(self.update_url, **self.gov_headers, data=self.data)

        assert response.status_code == 400
        assert response.json()["errors"] == {"default_queue": ["select a valid queue for team"]}

    def test_gov_user_update_existing_email(self):
        self.data["email"] = self.gov_user.email
        response = self.client.patch(self.update_url, **self.gov_headers, data=self.data)

        assert response.status_code == 400
        assert response.json()["errors"] == {"email": {"email": ["This email has already been registered"]}}

    def test_gov_user_update_bad_data(self):
        self.data["status"] = "bad_status"

        response = self.client.put(self.update_url, **self.gov_headers, data=self.data)

        assert response.status_code == 400
        assert response.json()["errors"] == {"status": ['"bad_status" is not a valid choice.']}

    @parameterized.expand(
        [
            (Roles.INTERNAL_SUPER_USER_ROLE_ID, {"email": "update@update.me"}, 200),  # /PS-IGNORE
            (Roles.INTERNAL_SUPER_USER_ROLE_ID, {"role": Roles.INTERNAL_SUPER_USER_ROLE_ID}, 200),
            (Roles.INTERNAL_SUPER_USER_ROLE_ID, {"default_queue": str(MY_TEAMS_QUEUES_CASES_ID)}, 200),
            (Roles.INTERNAL_DEFAULT_ROLE_ID, {"default_queue": str(MY_TEAMS_QUEUES_CASES_ID)}, 403),
            (
                Roles.INTERNAL_DEFAULT_ROLE_ID,
                {"role": Roles.INTERNAL_SUPER_USER_ROLE_ID, "default_queue": str(MY_TEAMS_QUEUES_CASES_ID)},
                403,
            ),
        ]
    )
    def test_gov_user_update_permission(self, role_id, data, expected_status):
        self.gov_user.role = Role.objects.get(id=role_id)
        self.gov_user.save()
        response = self.client.patch(self.update_url, **self.gov_headers, data=data)
        assert response.status_code == expected_status

    @parameterized.expand(
        [
            ({"default_queue": str(MY_TEAMS_QUEUES_CASES_ID)}, 200),
            (
                {"role": Roles.INTERNAL_SUPER_USER_ROLE_ID, "default_queue": str(MY_TEAMS_QUEUES_CASES_ID)},
                403,
            ),
        ]
    )
    def test_gov_user_update_self_non_super_user_permission(self, data, expected_status):
        self.gov_user.role = Role.objects.get(id=Roles.INTERNAL_DEFAULT_ROLE_ID)
        self.gov_user.save()
        url = reverse("caseworker_gov_users:update", kwargs={"pk": self.gov_user.pk})
        response = self.client.patch(url, **self.gov_headers, data=data)
        assert response.status_code == expected_status

    @parameterized.expand([(GovUserStatuses.DEACTIVATED, 0), (GovUserStatuses.ACTIVE, 1)])
    def test_gov_user_deactivate(self, user_status, expected):
        self.case.queues.set([self.queue])
        self.create_case_assignment(self.queue, self.case, [self.gov_user_edit])

        assert self.gov_user_edit.case_assignments.all().count() == 1

        response = self.client.patch(self.update_url, **self.gov_headers, data={"status": user_status})
        assert response.status_code == 200
        self.gov_user_edit.refresh_from_db()
        assert self.gov_user_edit.status == user_status
        assert self.gov_user_edit.case_assignments.all().count() == expected
