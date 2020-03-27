from faker import Faker
from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from addresses.tests.factories import ForeignAddressFactory
from conf.authentication import EXPORTER_USER_TOKEN_HEADER
from conf.constants import Roles, GovPermissions
from conf.helpers import date_to_drf_date
from lite_content.lite_api.strings import Organisations
from organisations.enums import OrganisationType, OrganisationStatus
from organisations.tests.factories import OrganisationFactory
from organisations.models import Organisation
from organisations.tests.providers import OrganisationProvider
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from test_helpers.helpers import generate_key_value_pair
from users.libraries.get_user import get_users_from_organisation
from users.libraries.user_to_token import user_to_token
from users.models import UserOrganisationRelationship


class OrganisationTests(DataTestClient):
    url = reverse("organisations:organisations")

    def test_list_organisations(self):
        organisation = OrganisationFactory()
        response = self.client.get(self.url, **self.gov_headers)
        response_data = next(data for data in response.json()["results"] if data["id"] == str(organisation.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data,
            {
                "id": str(organisation.id),
                "name": organisation.name,
                "sic_number": organisation.sic_number,
                "eori_number": organisation.eori_number,
                "type": generate_key_value_pair(organisation.type, OrganisationType.choices),
                "registration_number": organisation.registration_number,
                "vat_number": organisation.vat_number,
                "status": generate_key_value_pair(organisation.status, OrganisationStatus.choices),
                "created_at": date_to_drf_date(organisation.created_at),
            },
        )

    def test_create_commercial_organisation_as_internal_success(self):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "01110",
            "vat_number": "GB1234567",
            "registration_number": "98765432",
            "site": {
                "name": "Headquarters",
                "address": {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "Queens Road",
                    "region": "Hertfordshire",
                    "postcode": "AL1 4GT",
                    "city": "St Albans",
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
        self.assertEqual(organisation.status, OrganisationStatus.ACTIVE)

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
        self.assertEqualIgnoreType(site.address.country.id, "GB")

    @parameterized.expand(
        [
            [
                {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "Queens Road",
                    "region": "Hertfordshire",
                    "postcode": "AL1 4GT",
                    "city": "St Albans",
                }
            ],
            [{"address": "123", "country": "PL"}],
        ]
    )
    def test_create_commercial_organisation_as_exporter_success(self, address):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "01110",
            "vat_number": "GB1234567",
            "registration_number": "98765432",
            "site": {"name": "Headquarters", "address": address},
            "user": {"email": "trinity@bsg.com"},
        }

        response = self.client.post(self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user)})
        organisation = Organisation.objects.get(id=response.json()["id"])
        exporter_user = get_users_from_organisation(organisation)[0]
        site = organisation.primary_site

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(organisation.name, data["name"])
        self.assertEqual(organisation.eori_number, data["eori_number"])
        self.assertEqual(organisation.sic_number, data["sic_number"])
        self.assertEqual(organisation.vat_number, data["vat_number"])
        self.assertEqual(organisation.registration_number, data["registration_number"])
        self.assertEqual(organisation.status, OrganisationStatus.IN_REVIEW)

        self.assertEqual(exporter_user.email, data["user"]["email"])
        self.assertEqual(
            UserOrganisationRelationship.objects.get(user=exporter_user, organisation=organisation).role_id,
            Roles.EXPORTER_SUPER_USER_ROLE_ID,
        )

        self.assertEqual(site.name, data["site"]["name"])

        if "address_line_1" in address:
            self.assertEqual(site.address.address_line_1, data["site"]["address"]["address_line_1"])
            self.assertEqual(site.address.address_line_2, data["site"]["address"]["address_line_2"])
            self.assertEqual(site.address.region, data["site"]["address"]["region"])
            self.assertEqual(site.address.postcode, data["site"]["address"]["postcode"])
            self.assertEqual(site.address.city, data["site"]["address"]["city"])
            self.assertEqualIgnoreType(site.address.country.id, "GB")
        else:
            self.assertEqual(site.address.address, data["site"]["address"]["address"])
            self.assertEqualIgnoreType(site.address.country.id, data["site"]["address"]["country"])

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
                },
            },
            "user": {"first_name": "Trinity", "last_name": "Fishburne", "email": "trinity@bsg.com"},
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([["GB1234567"], [""]])
    def test_create_organisation_as_a_private_individual(self, vat_number):
        data = {
            "name": "John Smith",
            "type": OrganisationType.INDIVIDUAL,
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
        self.assertEqualIgnoreType(site.address.country.id, "GB")

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
        self.assertEqualIgnoreType(site.address.country.id, "GB")

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
        ]
    )
    def test_list_filter_organisations_by_name_and_type(self, name, org_types, expected_result):
        # Add organisations to filter
        OrganisationFactory(name="Individual", type=OrganisationType.INDIVIDUAL)
        OrganisationFactory(name="Commercial", type=OrganisationType.COMMERCIAL)
        OrganisationFactory(name="HMRC", type=OrganisationType.HMRC)

        org_types_param = ""
        for org_type in org_types:
            org_types_param += "&org_type=" + org_type

        response = self.client.get(self.url + "?search_term=" + name + org_types_param, **self.gov_headers)

        self.assertEqual(len(response.json()["results"]), expected_result)


class EditOrganisationTests(DataTestClient):
    faker = Faker()
    faker.add_provider(OrganisationProvider)

    def _get_url(self, org_id):
        return reverse("organisations:organisation", kwargs={"pk": org_id})

    def test_set_org_details_success(self):
        """
        Internal users can change an organisation's information
        """
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])
        data = {
            "eori_number": self.faker.eori_number(),
            "sic_number": self.faker.sic_number(),
            "vat_number": self.faker.vat_number(),
            "registration_number": self.faker.registration_number(),
        }

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(organisation.eori_number, data["eori_number"])
        self.assertEqual(organisation.sic_number, data["sic_number"])
        self.assertEqual(organisation.vat_number, data["vat_number"])
        self.assertEqual(organisation.registration_number, data["registration_number"])

    def test_set_org_details_to_none_uk_address_failure(self):
        """
        Organisations based in the UK need to provide all details about themselves
        """
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])
        data = {
            "eori_number": None,
            "sic_number": None,
            "vat_number": None,
            "registration_number": None,
        }

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(organisation.eori_number)
        self.assertIsNotNone(organisation.sic_number)
        self.assertIsNotNone(organisation.vat_number)
        self.assertIsNotNone(organisation.registration_number)

    def test_set_org_details_to_none_foreign_address_success(self):
        """
        Organisations based in foreign countries don't need to provide
        all details about themselves
        """
        organisation = OrganisationFactory(
            type=OrganisationType.COMMERCIAL, primary_site__address=ForeignAddressFactory(),
        )
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])
        data = {
            "eori_number": None,
            "sic_number": None,
            "vat_number": None,
            "registration_number": None,
        }

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(organisation.eori_number)
        self.assertIsNone(organisation.sic_number)
        self.assertIsNone(organisation.vat_number)
        self.assertIsNone(organisation.registration_number)

    def test_cannot_edit_organisation_without_permission(self):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.clear()
        data = {"name": self.faker.company()}

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], Organisations.NO_PERM_TO_EDIT)
        self.assertNotEqual(organisation.name, data["name"])

    def test_can_edit_name_with_manage_and_reopen_permissions(self):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )
        data = {"name": self.faker.company()}

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["organisation"]["name"], data["name"])
        self.assertEqual(organisation.name, data["name"])

    def test_no_name_change_to_org_does_not_reopen_finalised_cases(self):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        case_one = self.create_standard_application_case(organisation, reference_name="Case one")
        case_two = self.create_standard_application_case(organisation, reference_name="Case two")

        # Set case to finalised and provide licence duration
        case_one.status = get_case_status_by_status("finalised")
        case_one.licence_duration = 12
        case_one.save()

        self.data = {"name": organisation.name}
        response = self.client.put(self._get_url(organisation.id), self.data, **self.gov_headers)
        case_one.refresh_from_db()
        case_two.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check no case status were updated as the org's name was not changed
        self.assertEqual(case_one.status.status, CaseStatusEnum.FINALISED)
        self.assertEqual(case_two.status.status, CaseStatusEnum.SUBMITTED)

    def test_name_change_to_org_reopens_finalised_cases(self):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        data = {"name": self.faker.company()}

        case_one = self.create_standard_application_case(organisation, reference_name="Case one")
        case_two = self.create_standard_application_case(organisation, reference_name="Case two")

        # Set case to finalised and provide licence duration
        case_one.status = get_case_status_by_status("finalised")
        case_one.licence_duration = 12
        case_one.save()

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        case_one.refresh_from_db()
        case_two.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check only the finalised case's status was changed
        self.assertEqual(case_one.status.status, CaseStatusEnum.REOPENED_DUE_TO_ORG_CHANGES)
        self.assertEqual(case_two.status.status, CaseStatusEnum.SUBMITTED)
