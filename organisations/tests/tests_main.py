from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from conf.constants import Roles, GovPermissions
from lite_content.lite_api.strings import Organisations
from organisations.enums import OrganisationType, OrganisationStatus
from organisations.models import Organisation
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from test_helpers.helpers import generate_key_value_pair
from users.libraries.get_user import get_users_from_organisation
from users.models import UserOrganisationRelationship


class OrganisationTests(DataTestClient):

    url = reverse("organisations:organisations")

    def test_list_organisations(self):
        organisation, _ = self.create_organisation_with_exporter_user("Anyone's Ghost Inc")
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualIgnoreType(response_data["id"], organisation.id)
        self.assertEqual(response_data["name"], organisation.name)
        self.assertEqual(response_data["sic_number"], organisation.sic_number)
        self.assertEqual(response_data["eori_number"], organisation.eori_number)
        self.assertEqual(response_data["type"], generate_key_value_pair(organisation.type, OrganisationType.choices))
        self.assertEqual(response_data["registration_number"], organisation.registration_number)
        self.assertEqual(response_data["vat_number"], organisation.vat_number)
        self.assertEqual(
            response_data["status"], generate_key_value_pair(organisation.status, OrganisationStatus.choices)
        )
        self.assertIn("created_at", response_data)
        self.assertEqual(len(response_data), 9)

    def test_create_commercial_organisation_as_internal_success(self):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "2765",
            "vat_number": "123456789",
            "registration_number": "987654321",
            "site": {
                "name": "Headquarters",
                "address": {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "Queens Road",
                    "region": "Hertfordshire",
                    "postcode": "AL1 4GT",
                    "city": "St Albans",
                    "country": "GB",
                },
            },
            "user": {"email": "trinity@bsg.com"},
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        organisation = Organisation.objects.get(name=data["name"])
        exporter_user = get_users_from_organisation(organisation)[0]
        site = organisation.primary_site

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(organisation.name, data["name"])
        self.assertEqual(organisation.eori_number, data["eori_number"])
        self.assertEqual(organisation.sic_number, data["sic_number"])
        self.assertEqual(organisation.vat_number, data["vat_number"])
        self.assertEqual(organisation.registration_number, data["registration_number"])
        self.assertEqual(Organisation.status, OrganisationStatus.ACTIVE)

        self.assertEqual(exporter_user.email, data["user"]["email"])
        self.assertEqual(
            UserOrganisationRelationship.objects.get(user=exporter_user, organisation=organisation).role_id,
            Roles.EXPORTER_SUPER_USER_ROLE_ID,
        )

        self.assertEqual(site.name, data["site"]["name"])
        self.assertEqual(site.address.address_line_1, data["site"]["address"]["address_line_1"])
        self.assertEqual(site.address.address_line_2, data["site"]["address"]["address_line_2"])
        self.assertEqual(site.address.region, data["site"]["address"]["region"])
        self.assertEqual(site.address.postcode, data["site"]["address"]["postcode"])
        self.assertEqual(site.address.city, data["site"]["address"]["city"])
        self.assertEqual(str(site.address.country.id), data["site"]["address"]["country"])

    def test_create_commercial_organisation_as_exporter_success(self):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "2765",
            "vat_number": "123456789",
            "registration_number": "987654321",
            "site": {
                "name": "Headquarters",
                "address": {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "Queens Road",
                    "region": "Hertfordshire",
                    "postcode": "AL1 4GT",
                    "city": "St Albans",
                    "country": "GB",
                },
            },
            "user": {"email": "trinity@bsg.com"},
        }

        response = self.client.post(self.url, data)
        organisation = Organisation.objects.get(name=data["name"])
        exporter_user = get_users_from_organisation(organisation)[0]
        site = organisation.primary_site

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(organisation.name, data["name"])
        self.assertEqual(organisation.eori_number, data["eori_number"])
        self.assertEqual(organisation.sic_number, data["sic_number"])
        self.assertEqual(organisation.vat_number, data["vat_number"])
        self.assertEqual(organisation.registration_number, data["registration_number"])
        self.assertEqual(Organisation.status, OrganisationStatus.IN_REVIEW)

        self.assertEqual(exporter_user.email, data["user"]["email"])
        self.assertEqual(
            UserOrganisationRelationship.objects.get(user=exporter_user, organisation=organisation).role_id,
            Roles.EXPORTER_SUPER_USER_ROLE_ID,
        )

        self.assertEqual(site.name, data["site"]["name"])
        self.assertEqual(site.address.address_line_1, data["site"]["address"]["address_line_1"])
        self.assertEqual(site.address.address_line_2, data["site"]["address"]["address_line_2"])
        self.assertEqual(site.address.region, data["site"]["address"]["region"])
        self.assertEqual(site.address.postcode, data["site"]["address"]["postcode"])
        self.assertEqual(site.address.city, data["site"]["address"]["city"])
        self.assertEqual(str(site.address.country.id), data["site"]["address"]["country"])

    def test_cannot_create_organisation_with_invalid_data(self):
        data = {
            "name": None,
            "type": "commercial",
            "eori_number": None,
            "sic_number": None,
            "vat_number": None,
            "registration_number": None,
            "site": {
                "name": None,
                "address": {
                    "country": None,
                    "address_line_1": None,
                    "address_line_2": None,
                    "region": None,
                    "postcode": None,
                    "city": None,
                },
            },
            "user": {"first_name": None, "last_name": None, "email": None, "password": None},
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            ["1234", "1234", "1234", ""],
            ["1234", "1234", "", "1234"],
            ["1234", "", "1234", "1234"],
            ["", "1234", "1234", "1234"],
        ]
    )
    def test_create_organisation_missing_fields_failure(self, eori_number, vat_number, sic_number, registration_number):
        data = {
            "name": "Lemonworld Co",
            "type": "commercial",
            "eori_number": eori_number,
            "sic_number": sic_number,
            "vat_number": vat_number,
            "registration_number": registration_number,
            "site": {
                "name": "Headquarters",
                "address": {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "Queens Road",
                    "region": "Hertfordshire",
                    "postcode": "AL1 4GT",
                    "city": "St Albans",
                    "country": "GB",
                },
            },
            "user": {"first_name": "Trinity", "last_name": "Fishburne", "email": "trinity@bsg.com"},
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([["1231234"], [""]])
    def test_create_organisation_as_a_private_individual(self, vat_number):
        data = {
            "name": "John Smith",
            "type": "individual",
            "eori_number": "1234567890",
            "vat_number": vat_number,
            "site": {
                "name": "Headquarters",
                "address": {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "Queens Road",
                    "region": "Hertfordshire",
                    "postcode": "AL1 4GT",
                    "city": "St Albans",
                    "country": "GB",
                },
            },
            "user": {"email": "john@smith.com"},
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        organisation = Organisation.objects.get(name=data["name"])
        exporter_user = get_users_from_organisation(organisation)[0]
        site = organisation.primary_site

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(organisation.name, data["name"])
        self.assertEqual(organisation.eori_number, data["eori_number"])
        self.assertEqual(organisation.vat_number, data["vat_number"])

        self.assertEqual(exporter_user.email, data["user"]["email"])

        self.assertEqual(site.name, data["site"]["name"])
        self.assertEqual(site.address.address_line_1, data["site"]["address"]["address_line_1"])
        self.assertEqual(site.address.address_line_2, data["site"]["address"]["address_line_2"])
        self.assertEqual(site.address.region, data["site"]["address"]["region"])
        self.assertEqual(site.address.postcode, data["site"]["address"]["postcode"])
        self.assertEqual(site.address.city, data["site"]["address"]["city"])
        self.assertEqual(str(site.address.country.id), data["site"]["address"]["country"])

    def test_create_hmrc_organisation(self):
        data = {
            "name": "hmrc organisation",
            "type": "hmrc",
            "site": {
                "name": "Headquarters",
                "address": {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "Queens Road",
                    "region": "Hertfordshire",
                    "postcode": "AL1 4GT",
                    "city": "St Albans",
                    "country": "GB",
                },
            },
            "user": {"email": "trinity@bsg.com"},
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        organisation = Organisation.objects.get(id=response.json()["id"])
        exporter_user = get_users_from_organisation(organisation)[0]
        site = organisation.primary_site

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(organisation.name, data["name"])

        self.assertEqual(exporter_user.email, data["user"]["email"])

        self.assertEqual(site.name, data["site"]["name"])
        self.assertEqual(site.address.address_line_1, data["site"]["address"]["address_line_1"])
        self.assertEqual(site.address.address_line_2, data["site"]["address"]["address_line_2"])
        self.assertEqual(site.address.region, data["site"]["address"]["region"])
        self.assertEqual(site.address.postcode, data["site"]["address"]["postcode"])
        self.assertEqual(site.address.city, data["site"]["address"]["city"])
        self.assertEqual(str(site.address.country.id), data["site"]["address"]["country"])

    @parameterized.expand(
        [
            ["indi", ["individual"], 1],
            ["indi", ["hmrc"], 0],
            ["indi", ["commercial"], 0],
            ["comm", ["individual"], 0],
            ["comm", ["hmrc"], 0],
            ["comm", ["commercial"], 1],
            ["hmr", ["individual"], 0],
            ["hmr", ["hmrc"], 2],
            ["hmr", ["commercial"], 0],
            ["al", ["commercial", "individual"], 2],  # multiple org types
            ["9876", ["individual"], 1],  # CRN as search term
        ]
    )
    def test_list_filter_organisations_by_name_and_type(self, name, org_types, expected_result):
        self.create_organisation_with_exporter_user("Individual", org_type="individual")
        self.create_organisation_with_exporter_user("Commercial", org_type="commercial")
        self.create_organisation_with_exporter_user("HMRC", org_type="hmrc")

        org_types_param = ""
        for org_type in org_types:
            org_types_param += "&org_type=" + org_type

        response = self.client.get(self.url + "?search_term=" + name + org_types_param, **self.gov_headers)

        self.assertEqual(len(response.json()["results"]), expected_result)


class EditOrganisationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.organisation, _ = self.create_organisation_with_exporter_user("An organisation")
        self.url = reverse("organisations:organisation", kwargs={"pk": self.organisation.id})

        self.org_name = "An organisation"
        self.new_org_name = "New org name"
        self.type = "commercial"
        self.eori_number = "123"
        self.sic_number = "456"
        self.vat_number = "789"
        self.registration_number = "111"

        self.original_org_eori_number = self.organisation.eori_number
        self.original_org_sic_number = self.organisation.sic_number
        self.original_org_vat_number = self.organisation.vat_number
        self.original_registration_number = self.organisation.registration_number

        self.data = {
            "name": self.org_name,
            "type": self.type,
            "eori_number": self.eori_number,
            "sic_number": self.sic_number,
            "vat_number": self.vat_number,
            "registration_number": self.registration_number,
            "user": {"email": "trinity@bsg.com"},
        }

    def test_can_edit_organisation_with_manage_org_permission(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])

        response = self.client.put(self.url, self.data, **self.gov_headers)
        response_data = response.json()["organisation"]
        self.organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["name"], self.org_name)
        self.assertEqual(response_data["type"], self.type)
        self.assertEqual(response_data["eori_number"], self.eori_number)
        self.assertEqual(response_data["sic_number"], self.sic_number)
        self.assertEqual(response_data["vat_number"], self.vat_number)
        self.assertEqual(response_data["registration_number"], self.registration_number)

        self.assertEqual(self.organisation.name, self.org_name)
        self.assertEqual(self.organisation.type, self.type)
        self.assertEqual(self.organisation.eori_number, self.eori_number)
        self.assertEqual(self.organisation.sic_number, self.sic_number)
        self.assertEqual(self.organisation.vat_number, self.vat_number)
        self.assertEqual(self.organisation.registration_number, self.registration_number)

    def test_cannot_edit_organisation_without_manage_org_permission(self):
        self.gov_user.role.permissions.clear()

        response = self.client.put(self.url, self.data, **self.gov_headers)
        response_data = response.json()["errors"]
        self.org_copy = self.organisation

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data, Organisations.NO_PERM_TO_EDIT)

        # Assert the organisation has not changed
        self.assertEqual(self.organisation.name, self.org_name)
        self.assertEqual(self.organisation.type, self.type)
        self.assertEqual(self.organisation.eori_number, self.original_org_eori_number)
        self.assertEqual(self.organisation.sic_number, self.original_org_sic_number)
        self.assertEqual(self.organisation.vat_number, self.original_org_vat_number)
        self.assertEqual(self.organisation.registration_number, self.original_registration_number)

    def test_can_edit_all_org_details_with_manage_and_reopen_permissions(self):
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        data = {
            "name": self.new_org_name,
            "type": self.type,
            "eori_number": self.eori_number,
            "sic_number": self.sic_number,
            "vat_number": self.vat_number,
            "registration_number": self.registration_number,
            "user": {"email": "trinity@bsg.com"},
        }

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()["organisation"]
        self.organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["name"], self.new_org_name)
        self.assertEqual(response_data["type"], self.type)
        self.assertEqual(response_data["eori_number"], self.eori_number)
        self.assertEqual(response_data["sic_number"], self.sic_number)
        self.assertEqual(response_data["vat_number"], self.vat_number)
        self.assertEqual(response_data["registration_number"], self.registration_number)

        self.assertEqual(self.organisation.name, self.new_org_name)
        self.assertEqual(self.organisation.type, self.type)
        self.assertEqual(self.organisation.eori_number, self.eori_number)
        self.assertEqual(self.organisation.sic_number, self.sic_number)
        self.assertEqual(self.organisation.vat_number, self.vat_number)
        self.assertEqual(self.organisation.registration_number, self.registration_number)

    def test_cannot_edit_org_name_without_all_required_permissions(self):
        """ Test that an organisations name cannot be edited if the user does not have both the 'Manage organisations'
        and 'Reopen closed cases' permissions.

        """
        self.gov_user.role.permissions.clear()
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])

        data = {
            "name": self.new_org_name,
            "type": self.type,
            "eori_number": self.eori_number,
            "sic_number": self.sic_number,
            "vat_number": self.vat_number,
            "registration_number": self.registration_number,
            "user": {"email": "trinity@bsg.com"},
        }

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()["errors"]
        self.organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data, Organisations.NO_PERM_TO_EDIT_NAME)

        # Assert the organisation has not changed
        self.assertEqual(self.organisation.name, self.org_name)
        self.assertEqual(self.organisation.type, self.type)
        self.assertEqual(self.organisation.eori_number, self.original_org_eori_number)
        self.assertEqual(self.organisation.sic_number, self.original_org_sic_number)
        self.assertEqual(self.organisation.vat_number, self.original_org_vat_number)
        self.assertEqual(self.organisation.registration_number, self.original_registration_number)

    def test_when_validate_only_org_is_not_edited(self):
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        self.data["validate_only"] = True

        response = self.client.put(self.url, self.data, **self.gov_headers)
        response_data = response.json()["organisation"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["name"], self.organisation.name)
        self.assertEqual(response_data["type"]["key"], self.organisation.type)
        self.assertEqual(response_data["eori_number"], self.organisation.eori_number)
        self.assertEqual(response_data["sic_number"], self.organisation.sic_number)
        self.assertEqual(response_data["vat_number"], self.organisation.vat_number)
        self.assertEqual(response_data["registration_number"], self.organisation.registration_number)

    def test_no_name_change_to_org_does_not_reopen_finalised_cases(self):
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        case_one = self.create_standard_application_case(self.organisation, reference_name="Case one")
        case_two = self.create_standard_application_case(self.organisation, reference_name="Case two")

        # Set case to finalised and provide licence duration
        case_one.status = get_case_status_by_status("finalised")
        case_one.licence_duration = 12
        case_one.save()

        response = self.client.put(self.url, self.data, **self.gov_headers)
        case_one.refresh_from_db()
        case_two.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check no case status were updated as the org's name was not changed
        self.assertEqual(case_one.status.status, CaseStatusEnum.FINALISED)
        self.assertEqual(case_two.status.status, CaseStatusEnum.SUBMITTED)

    def test_name_change_to_org_reopens_finalised_cases(self):
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        data = {
            "name": self.new_org_name,
            "type": self.type,
            "eori_number": self.eori_number,
            "sic_number": self.sic_number,
            "vat_number": self.vat_number,
            "registration_number": self.registration_number,
            "user": {"email": "trinity@bsg.com"},
        }

        case_one = self.create_standard_application_case(self.organisation, reference_name="Case one")
        case_two = self.create_standard_application_case(self.organisation, reference_name="Case two")

        # Set case to finalised and provide licence duration
        case_one.status = get_case_status_by_status("finalised")
        case_one.licence_duration = 12
        case_one.save()

        response = self.client.put(self.url, data, **self.gov_headers)
        case_one.refresh_from_db()
        case_two.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check only the finalised case's status was changed
        self.assertEqual(case_one.status.status, CaseStatusEnum.REOPENED_DUE_TO_ORG_CHANGES)
        self.assertEqual(case_two.status.status, CaseStatusEnum.SUBMITTED)
