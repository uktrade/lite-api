from django.urls import reverse
from rest_framework import status

from api.parties.enums import PartyType
from test_helpers.clients import DataTestClient
from api.teams.tests.factories import TeamFactory
from api.teams.models import Department


class DataWorkspaceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.create_party("Test Party", self.organisation, PartyType.END_USER)

    def test_organisations(self):
        url = reverse("data_workspace:dw-organisations-list")
        expected_fields = (
            "id",
            "primary_site",
            "type",
            "flags",
            "status",
            "documents",
            "created_at",
            "updated_at",
            "name",
            "eori_number",
            "sic_number",
            "vat_number",
            "registration_number",
            "phone_number",
            "website",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_parties(self):
        url = reverse("data_workspace:dw-parties-list")
        expected_fields = (
            "id",
            "created_at",
            "updated_at",
            "name",
            "address",
            "website",
            "signatory_name_euu",
            "type",
            "role",
            "role_other",
            "sub_type",
            "sub_type_other",
            "clearance_level",
            "descriptors",
            "phone_number",
            "email",
            "details",
            "country",
            "organisation",
            "copy_of",
            "flags",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_queues(self):
        url = reverse("data_workspace:dw-queues-list")
        expected_fields = ("id", "name", "team", "countersigning_queue")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_teams(self):
        url = reverse("data_workspace:dw-teams-list")
        expected_fields = ("id", "name", "part_of_ecju", "is_ogd")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_departments(self):
        team = TeamFactory()
        url = reverse("data_workspace:dw-departments-list")
        response = self.client.get(url)
        payload = response.json()

        # Ensure we get departments and not sth else
        deps_ids = [d["id"] for d in payload["results"]]
        assert str(team.department.id) in deps_ids
        assert not str(team.id) in deps_ids
        assert len(deps_ids) == Department.objects.count()

        # Ensure we get some expected fields
        expected_fields = {"id", "name"}
        assert set(payload["results"][0].keys()) == expected_fields
