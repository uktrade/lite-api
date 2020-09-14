from faker import Faker
from rest_framework import status
from rest_framework.reverse import reverse

from api.audit_trail.models import Audit
from lite_content.lite_api import strings
from api.organisations.models import Site
from api.organisations.tests.factories import OrganisationFactory
from test_helpers.clients import DataTestClient
from api.users.models import UserOrganisationRelationship

faker = Faker()


class OrganisationSitesTests(DataTestClient):
    def test_site_list(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        # Create an additional organisation and site to ensure that only sites from the first organisation are shown
        OrganisationFactory()

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["sites"]), 1)

        response_site = response_data["sites"][0]
        primary_site = self.organisation.primary_site

        self.assertEqual(response_site["id"], str(primary_site.id))
        self.assertEqual(response_site["name"], str(primary_site.name))
        self.assertEqual(response_site["address"]["id"], str(primary_site.address.id))

    def test_get_site_list_with_total_users(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id}) + "?get_total_users=True"

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["sites"]), 1)
        self.assertEqual(response_data["sites"][0]["assigned_users_count"], 1)

    def test_view_site(self):
        user = self.create_exporter_user(self.organisation)
        UserOrganisationRelationship.objects.get(user=user).sites.add(self.organisation.primary_site)
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        url = reverse(
            "organisations:site", kwargs={"org_pk": self.organisation.id, "pk": self.organisation.primary_site_id}
        )

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["name"], self.organisation.primary_site.name)
        self.assertEqual(
            response_data["users"],
            [{"id": str(user.pk), "first_name": user.first_name, "last_name": user.last_name, "email": user.email,}],
        )
        self.assertEqual(
            response_data["admin_users"],
            [
                {
                    "id": str(self.exporter_user.pk),
                    "first_name": self.exporter_user.first_name,
                    "last_name": self.exporter_user.last_name,
                    "email": self.exporter_user.email,
                }
            ],
        )

    def test_add_uk_site(self):
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "records_located_step": True,
            "site_records_stored_here": True,
            "address": {
                "address_line_1": "a street",
                "city": "london",
                "postcode": "E14GH",
                "region": "Hertfordshire",
            },
        }

        response = self.client.post(url, data, **self.gov_headers)
        response_data = response.json()["site"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 2)
        site = Site.objects.get(name=data["name"])
        # Assert that "records_located_at" is set to the site being created
        self.assertEqual(
            response_data["records_located_at"],
            {
                "id": str(site.id),
                "name": site.name,
                "address": {
                    "address_line_1": site.address.address_line_1,
                    "address_line_2": site.address.address_line_2,
                    "city": site.address.city,
                    "country": {"name": site.address.country.name},
                    "postcode": site.address.postcode,
                    "region": site.address.region,
                },
            },
        )
        self.assertEqual(Audit.objects.count(), 1)

    def test_add_uk_site_no_site_record_location_error(self):
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "records_located_step": True,
            "address": {
                "address_line_1": "a street",
                "city": "london",
                "postcode": "E14GH",
                "region": "Hertfordshire",
            },
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"site_records_stored_here": [strings.Site.NO_RECORDS_LOCATED_AT]})
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 1)
        self.assertEqual(Audit.objects.count(), 0)

    def test_add_uk_site_site_record_location_no_and_not_selected_error(self):
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "records_located_step": True,
            "site_records_stored_here": False,
            "address": {
                "address_line_1": "a street",
                "city": "london",
                "postcode": "E14GH",
                "region": "Hertfordshire",
            },
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"site_records_located_at": [strings.Site.NO_SITE_SELECTED]})
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 1)
        self.assertEqual(Audit.objects.count(), 0)

    def test_add_uk_site_with_records_held_at_another_site_success(self):
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "records_located_step": True,
            "site_records_stored_here": "False",
            "site_records_located_at": self.organisation.primary_site.id,
            "address": {
                "address_line_1": "a street",
                "city": "london",
                "postcode": "E14GH",
                "region": "Hertfordshire",
            },
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 2)
        self.assertEqual(response.json()["site"]["records_located_at"]["name"], self.organisation.primary_site.name)
        self.assertEqual(Audit.objects.count(), 1)

    def test_add_uk_site_and_assign_users(self):
        exporter_user = self.create_exporter_user(self.organisation)
        exporter_user_2 = self.create_exporter_user(self.organisation)
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "address": {
                "address_line_1": "a street",
                "city": "london",
                "postcode": "E14GH",
                "region": "Hertfordshire",
            },
            "users": [exporter_user.pk, exporter_user_2.pk],
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        site = Site.objects.get(name=data["name"])
        self.assertEqual(site.users.count(), 2)

    def test_add_foreign_site(self):
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "address": {"address": "a street", "country": "PL",},
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 2)

    def test_add_foreign_site_failure(self):
        """
        Fail as only supplying an address field with country set to GB
        """
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "address": {"address": "a street", "country": "GB",},
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 1)

    def test_add_uk_and_foreign_site_failure(self):
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {
            "name": "regional site",
            "address": {
                "address_line_1": "a street",
                "city": "london",
                "postcode": "E14GH",
                "region": "Hertfordshire",
                "country": "GB",
                "address": "a street",
            },
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 1)

    def test_cannot_add_site_without_permission(self):
        number_of_initial_sites = Site.objects.count()
        url = reverse("organisations:sites", kwargs={"org_pk": self.organisation.id})

        data = {}
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Site.objects.count(), number_of_initial_sites)


class SitesUpdateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.data = {"name": faker.word()}
        self.url = reverse(
            "organisations:site", kwargs={"org_pk": self.organisation.id, "pk": self.organisation.primary_site.id}
        )

    def test_edit_site_name_success(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

        response = self.client.patch(self.url, self.data, **self.exporter_headers)
        self.organisation.primary_site.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.organisation.primary_site.name, self.data["name"])

    def test_edit_site_without_permission_failure(self):
        response = self.client.patch(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(self.organisation.primary_site.name, self.data["name"])

    def test_edit_site_records_location_not_set_failure(self):
        self.data = {}
        response = self.client.patch(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"site_records_stored_here": [strings.Site.NO_RECORDS_LOCATED_AT]})

    def test_edit_site_records_held_at_another_location_site_not_chosen_failure(self):
        self.data = {"site_records_stored_here": False}
        response = self.client.patch(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"site_records_located_at": [strings.Site.NO_SITE_SELECTED]})

    def test_edit_site_name_site_already_used_on_an_application_failure(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        self.organisation.primary_site.is_used_on_application = True
        self.organisation.primary_site.save()

        response = self.client.patch(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(self.organisation.primary_site.name, self.data["name"])
        self.assertEqual(
            response.json()["errors"], {"site_records_stored_here": [strings.Site.CANNOT_CHANGE_SITE_IF_ALREADY_IN_USE]}
        )

    def test_edit_site_records_location_site_already_used_on_an_application_failure(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        self.organisation.primary_site.is_used_on_application = True
        self.organisation.primary_site.save()
        self.data = {"records_located_step": True, "site_records_stored_here": True}

        response = self.client.patch(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"], {"site_records_stored_here": [strings.Site.CANNOT_CHANGE_SITE_IF_ALREADY_IN_USE]}
        )
