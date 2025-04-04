import pytest

from unittest import mock
from faker import Faker
from parameterized import parameterized

from rest_framework import status
from rest_framework.reverse import reverse

from api.addresses.tests.factories import ForeignAddressFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.core.authentication import EXPORTER_USER_TOKEN_HEADER
from api.core.constants import Roles, GovPermissions
from lite_content.lite_api.strings import Organisations
from api.organisations.enums import OrganisationType, OrganisationStatus
from api.organisations.tests.factories import OrganisationFactory
from api.organisations.models import Organisation
from api.organisations.tests.providers import OrganisationProvider
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from test_helpers.helpers import generate_key_value_pair
from api.users.libraries.get_user import get_users_from_organisation
from api.users.libraries.user_to_token import user_to_token
from api.users.models import UserOrganisationRelationship
from api.users.tests.factories import UserOrganisationRelationshipFactory
from api.addresses.tests.factories import AddressFactoryGB


class GetOrganisationTests(DataTestClient):
    url = reverse("organisations:organisations")

    def test_list_organisations(self):
        organisation = OrganisationFactory()
        response = self.client.get(self.url, **self.gov_headers)
        response_data = next(data for data in response.json()["results"] if data["id"] == str(organisation.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = {
            "id",
            "name",
            "sic_number",
            "eori_number",
            "type",
            "registration_number",
            "vat_number",
            "status",
            "created_at",
        }
        assert response_data.keys() == expected_fields
        assert response_data["id"] == str(organisation.id)
        assert response_data["name"] == organisation.name
        assert response_data["sic_number"] == organisation.sic_number
        assert response_data["eori_number"] == organisation.eori_number
        assert response_data["type"] == generate_key_value_pair(organisation.type, OrganisationType.choices)
        assert response_data["registration_number"] == organisation.registration_number
        assert response_data["vat_number"] == organisation.vat_number
        assert response_data["status"] == generate_key_value_pair(organisation.status, OrganisationStatus.choices)
        assert response_data["created_at"]

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
    @pytest.mark.xfail(reason="Failing randomly, marking as fail temporarily")
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

    def test_list_filter_organisations_by_status(self):
        self.organisation_1 = OrganisationFactory(status=OrganisationStatus.IN_REVIEW)
        self.organisation_2 = OrganisationFactory(status=OrganisationStatus.REJECTED)
        self.organisation_3 = OrganisationFactory(status=OrganisationStatus.ACTIVE)

        response = self.client.get(self.url + "?status=" + OrganisationStatus.ACTIVE, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all([item["status"]["key"] == OrganisationStatus.ACTIVE for item in response_data]))


class CreateOrganisationTests(DataTestClient):
    url = reverse("organisations:organisations")

    @mock.patch("api.organisations.notify.notify_caseworker_new_registration")
    @mock.patch("api.organisations.notify.notify_exporter_registration")
    def test_create_commercial_organisation_as_internal_success(
        self, mocked_notify_exporter_registration, mocked_caseworker_new_registration
    ):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "01110",
            "vat_number": "GB123456789",
            "phone_number": "+441234567895",
            "website": "",
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        organisation = Organisation.objects.get(name=data["name"])
        exporter_user = get_users_from_organisation(organisation)[0]
        site = organisation.primary_site

        self.assertEqual(organisation.name, data["name"])
        self.assertEqual(organisation.eori_number, data["eori_number"])
        self.assertEqual(organisation.sic_number, data["sic_number"])
        self.assertEqual(organisation.vat_number, data["vat_number"])
        self.assertEqual(organisation.registration_number, data["registration_number"])
        self.assertEqual(organisation.phone_number, data["phone_number"])
        self.assertEqual(organisation.status, OrganisationStatus.ACTIVE)

        self.assertEqual(exporter_user.email, data["user"]["email"])
        self.assertEqual(
            UserOrganisationRelationship.objects.get(user=exporter_user, organisation=organisation).role_id,
            Roles.EXPORTER_ADMINISTRATOR_ROLE_ID,
        )

        self.assertEqual(site.name, data["site"]["name"])
        self.assertEqual(site.address.address_line_1, data["site"]["address"]["address_line_1"])
        self.assertEqual(site.address.address_line_2, data["site"]["address"]["address_line_2"])
        self.assertEqual(site.address.region, data["site"]["address"]["region"])
        self.assertEqual(site.address.postcode, data["site"]["address"]["postcode"])
        self.assertEqual(site.address.city, data["site"]["address"]["city"])
        self.assertEqualIgnoreType(site.address.country.id, "GB")
        self.assertEqual(Audit.objects.count(), 1)

        # Ensure that exporters are not notified when an internal user creates an organisation
        assert not mocked_notify_exporter_registration.called
        # Caseworkers are still notified
        mocked_caseworker_new_registration.called_with(
            {"organisation_name": data["name"], "applicant_email": data["user"]["email"]}
        )

    @parameterized.expand(
        [
            [
                {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "Queens Road",
                    "region": "Hertfordshire",
                    "postcode": "AL1 4GT",
                    "city": "St Albans",
                },
            ],
            [{"address": "123", "country": "PL"}],
        ]
    )
    @mock.patch("api.organisations.notify.notify_exporter_registration")
    @mock.patch("api.organisations.notify.notify_caseworker_new_registration")
    def test_create_commercial_organisation_as_exporter_success(
        self,
        address,
        mocked_notify_caseworker_new_registration,
        mocked_notify_exporter_registration,
    ):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "01110",
            "vat_number": "GB123456789",
            "registration_number": "98765432",
            "phone_number": "+441234567895",
            "website": "",
            "site": {"name": "Headquarters", "address": address},
            "user": {"email": "trinity@bsg.com"},
        }

        response = self.client.post(
            self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        organisation = Organisation.objects.get(id=response.json()["id"])
        exporter_user = get_users_from_organisation(organisation)[0]
        site = organisation.primary_site

        self.assertEqual(organisation.name, data["name"])
        self.assertEqual(organisation.eori_number, data["eori_number"])
        self.assertEqual(organisation.sic_number, data["sic_number"])
        self.assertEqual(organisation.vat_number, data["vat_number"])
        self.assertEqual(organisation.registration_number, data["registration_number"])
        self.assertEqual(organisation.status, OrganisationStatus.IN_REVIEW)

        self.assertEqual(exporter_user.email, data["user"]["email"])
        self.assertEqual(
            UserOrganisationRelationship.objects.get(user=exporter_user, organisation=organisation).role_id,
            Roles.EXPORTER_ADMINISTRATOR_ROLE_ID,
        )

        self.assertEqual(site.name, data["site"]["name"])
        self.assertEqual(Audit.objects.count(), 1)

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

        # assert records located at set to site itself
        self.assertEqual(site.site_records_located_at, site)

        mocked_notify_exporter_registration.assert_called_with(
            data["user"]["email"], {"organisation_name": data["name"]}
        )
        mocked_notify_caseworker_new_registration.assert_called_with(
            {"organisation_name": data["name"], "applicant_email": data["user"]["email"]}
        )

    def test_create_commercial_organisation_as_exporter_success_with_previously_rejected_or_draft_crn(self):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "01110",
            "vat_number": "GB123456789",
            "registration_number": "98765432",
            "phone_number": "+441234567895",
            "website": "",
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
        response = self.client.post(
            self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        organisation = Organisation.objects.get(id=response.json()["id"])
        organisation.status = OrganisationStatus.REJECTED
        organisation.save()
        response = self.client.post(
            self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        organisation = Organisation.objects.get(id=response.json()["id"])
        organisation.status = OrganisationStatus.DRAFT
        organisation.save()
        response = self.client.post(
            self.url, data, **{EXPORTER_USER_TOKEN_HEADER: user_to_token(self.exporter_user.baseuser_ptr)}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_organisation_phone_number_mandatory(self):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "01110",
            "vat_number": "GB123456789",
            "registration_number": "98765432",
            "phone_number": "",
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.json()["errors"]
        self.assertEqual(errors["phone_number"][0], "Enter an organisation telephone number")

        data["type"] = OrganisationType.INDIVIDUAL
        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.json()["errors"]
        self.assertEqual(errors["phone_number"][0], "Enter a telephone number")

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
        self.assertEqual(Audit.objects.count(), 0)

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
        self.assertEqual(Audit.objects.count(), 0)

    def test_create_organisation_unique_company_failure(self):
        data = {
            "name": "Lemonworld Co",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": "01110",
            "vat_number": "GB123456789",
            "registration_number": "12345678",
            "phone_number": "+441234567895",
            "website": "",
            "site": {
                "name": "Headquarters",
                "address": {
                    "address_line_1": "42 Industrial Estate",
                    "address_line_2": "Queens Road",
                    "region": "Hertfordshire",
                    "city": "St Albans",
                },
            },
            "user": {"email": "trinity@bsg.com"},
        }

        response_1 = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response_1.status_code, status.HTTP_201_CREATED)

        response_2 = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response_2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_2.json(), {"errors": {"registration_number": ["This registration number is already in use."]}}
        )

    @parameterized.expand([["GB123456789"], [""]])
    def test_create_organisation_as_a_private_individual(self, vat_number):
        data = {
            "name": "John Smith",
            "type": OrganisationType.INDIVIDUAL,
            "eori_number": "GB123456789000",
            "vat_number": vat_number,
            "phone_number": "+441234567895",
            "website": "",
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
        self.assertEqual(site.site_records_located_at, site)
        self.assertEqualIgnoreType(site.address.country.id, "GB")
        self.assertEqual(Audit.objects.count(), 1)

    def test_create_hmrc_organisation(self):
        data = {
            "name": "hmrc organisation",
            "type": "hmrc",
            "phone_number": "+441234567895",
            "website": "",
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        organisation = Organisation.objects.get(id=response.json()["id"])
        exporter_user = get_users_from_organisation(organisation)[0]
        site = organisation.primary_site

        self.assertEqual(organisation.name, data["name"])

        self.assertEqual(exporter_user.email, data["user"]["email"])

        self.assertEqual(site.name, data["site"]["name"])
        self.assertEqual(site.address.address_line_1, data["site"]["address"]["address_line_1"])
        self.assertEqual(site.address.address_line_2, data["site"]["address"]["address_line_2"])
        self.assertEqual(site.address.region, data["site"]["address"]["region"])
        self.assertEqual(site.address.postcode, data["site"]["address"]["postcode"])
        self.assertEqual(site.address.city, data["site"]["address"]["city"])
        self.assertEqualIgnoreType(site.address.country.id, "GB")
        self.assertEqual(Audit.objects.count(), 1)


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
        previous_eori_number = organisation.eori_number
        previous_sic_number = organisation.sic_number
        previous_vat_number = organisation.vat_number
        previous_registration_number = organisation.registration_number

        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])
        data = {
            "eori_number": "GB123456789000",
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

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 4)
        for audit in audit_qs:
            verb = AuditType.UPDATED_ORGANISATION
            self.assertEqual(AuditType(audit.verb), verb)
            if audit.payload["key"] == "registration number":
                org_field = "registration number"
                previous_value = previous_registration_number
                new_value = organisation.registration_number
            elif audit.payload["key"] == "VAT number":
                org_field = "VAT number"
                previous_value = previous_vat_number
                new_value = organisation.vat_number
            elif audit.payload["key"] == "SIC number":
                org_field = "SIC number"
                previous_value = previous_sic_number
                new_value = organisation.sic_number
            elif audit.payload["key"] == "EORI number":
                org_field = "EORI number"
                previous_value = previous_eori_number
                new_value = organisation.eori_number

            payload = {"key": org_field, "old": previous_value, "new": new_value}
            self.assertEqual(audit.payload, payload)

    def test_set_org_details_to_none_uk_address_failure(self):
        """
        Organisations based in the UK need to provide all details about themselves
        """

        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        site = organisation.site.last()
        site.address = AddressFactoryGB()
        site.save()

        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])
        data = {"eori_number": None, "sic_number": None, "vat_number": None, "registration_number": None}

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(organisation.eori_number)
        self.assertIsNotNone(organisation.sic_number)
        self.assertIsNotNone(organisation.vat_number)
        self.assertIsNotNone(organisation.registration_number)
        self.assertEqual(Audit.objects.count(), 0)

    def test_set_org_details_to_none_foreign_address_success(self):
        """
        Organisations based in foreign countries don't need to provide
        all details about themselves
        """
        organisation = OrganisationFactory(
            type=OrganisationType.COMMERCIAL, primary_site__address=ForeignAddressFactory()
        )
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])
        data = {"eori_number": None, "sic_number": None, "vat_number": None, "registration_number": None}

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(organisation.eori_number)
        self.assertIsNone(organisation.sic_number)
        self.assertIsNone(organisation.vat_number)
        self.assertIsNone(organisation.registration_number)
        self.assertEqual(Audit.objects.count(), 4)

    def test_cannot_edit_organisation_without_permission(self):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.clear()
        data = {"name": self.faker.company()}

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        organisation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], Organisations.NO_PERM_TO_EDIT)
        self.assertNotEqual(organisation.name, data["name"])
        self.assertEqual(Audit.objects.count(), 0)

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
        self.assertEqual(Audit.objects.count(), 1)

    def test_no_name_change_to_org_does_not_reopen_finalised_cases(self):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        case_one = self.create_standard_application_case(
            organisation, reference_name="Case one", user=self.exporter_user
        )
        case_two = self.create_standard_application_case(
            organisation, reference_name="Case two", user=self.exporter_user
        )

        # Set case to finalised and provide licence duration
        case_one.status = get_case_status_by_status("finalised")
        case_one.licence_duration = 12
        case_one.save()

        self.data = {"name": organisation.name}
        response = self.client.put(self._get_url(organisation.id), self.data, **self.gov_headers)
        case_one.refresh_from_db()
        case_two.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Audit.objects.count(), 2)

        # Check no case status were updated as the org's name was not changed
        self.assertEqual(case_one.status.status, CaseStatusEnum.FINALISED)
        self.assertEqual(case_two.status.status, CaseStatusEnum.SUBMITTED)

    def test_name_change_to_org_reopens_finalised_cases(self):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        data = {"name": self.faker.company()}

        case_one = self.create_standard_application_case(
            organisation, reference_name="Case one", user=self.exporter_user
        )
        case_two = self.create_standard_application_case(
            organisation, reference_name="Case two", user=self.exporter_user
        )

        # Set case to finalised and provide licence duration
        case_one.status = get_case_status_by_status("finalised")
        case_one.licence_duration = 12
        case_one.save()

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        case_one.refresh_from_db()
        case_two.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Audit.objects.count(), 3)

        # Check only the finalised case's status was changed
        self.assertEqual(case_one.status.status, CaseStatusEnum.REOPENED_DUE_TO_ORG_CHANGES)
        self.assertEqual(case_two.status.status, CaseStatusEnum.SUBMITTED)

    @parameterized.expand(
        [
            "GB517182944",
            "GB999999973",
            "GB123456789",
            "GBGD600",
            "GBHA244",
            "GB123456789123",
            "GBHA324",
            "GB124 555 777",
            "GB 123 456 789",
            "GB12 3456 789",
            "GB1 23 45 67 89",
            "GB12 345 67 89 012",
            "GB-123-456-789",
            "GB-12345-6789101",
            "GBH A125",
            "GB GD 123",
            "GB GD123",
            "XI517182944",
            "XI999999973",
            "XI123456789",
            "XIGD600",
            "XIHA244",
            "XI123456789123",
            "XIHA324",
            "XI124 555 777",
            "XI 123 456 789",
            "XI12 3456 789",
            "XI1 23 45 67 89",
            "XI12 345 67 89 012",
            "XI-123-456-789",
            "XI-12345-6789101",
            "XIH A125",
            "XI GD 123",
            "XI GD123",
        ],
    )
    def test_vat_number_is_valid(self, vat_number):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        data = {
            "name": "regional site",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": self.faker.sic_number(),
            "vat_number": vat_number,
            "registration_number": self.faker.registration_number(),
            "phone_number": "+441234567999",
            "website": "",
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

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @parameterized.expand(
        [
            ("GB1234567", ["Invalid UK VAT number"]),
            ("GBGD6731890", ["Invalid UK VAT number"]),
            ("GB12345678910111313", ["Standard UK VAT numbers are 9 digits long"]),
            ("GBHA424GB123456789123", ["Standard UK VAT numbers are 9 digits long"]),
            ("GB  1234567", ["Invalid UK VAT number"]),
            ("GB GD1378", ["Invalid UK VAT number"]),
            ("GBDG673", ["Invalid UK VAT number"]),
            ("GBAH839", ["Invalid UK VAT number"]),
            ("GB  HA 1324", ["Invalid UK VAT number"]),
            ("XI1234567", ["Invalid UK VAT number"]),
            ("XIGD6731890", ["Invalid UK VAT number"]),
            ("XI12345678910111313", ["Standard UK VAT numbers are 9 digits long"]),
            ("XIHA424XI123456789123", ["Standard UK VAT numbers are 9 digits long"]),
            ("XI  1234567", ["Invalid UK VAT number"]),
            ("XI GD1378", ["Invalid UK VAT number"]),
            ("XIDG673", ["Invalid UK VAT number"]),
            ("XIAH839", ["Invalid UK VAT number"]),
            ("XI  HA 1324", ["Invalid UK VAT number"]),
        ],
    )
    def test_vat_number_is_invalid(self, vat_number, expected_errors):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        data = {
            "name": "regional site",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": self.faker.sic_number(),
            "vat_number": vat_number,
            "registration_number": self.faker.registration_number(),
            "phone_number": "+441234567999",
            "website": "",
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

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["vat_number"],
            expected_errors,
        )

    @parameterized.expand(
        [
            ["GB123456789000", True, None],
            ["XI123456789000", True, None],
            ["GB1234567890001", False, ["Invalid UK EORI number"]],
            ["XI1234567890001", False, ["Invalid UK EORI number"]],
            ["GB12345678900012", False, ["Invalid UK EORI number"]],
            ["XI12345678900012", False, ["Invalid UK EORI number"]],
            ["GB123456789000123", True, None],
            ["XI123456789000123", True, None],
            ["GB12345678900", False, ["Invalid UK EORI number"]],
            ["XI12345678900", False, ["Invalid UK EORI number"]],
            ["GB1234567890001234", False, ["EORI numbers are 17 characters or less"]],
            ["XI1234567890001234", False, ["EORI numbers are 17 characters or less"]],
            ["GB-123456789-0", False, ["Invalid UK EORI number"]],
            ["XI-123456789-0", False, ["Invalid UK EORI number"]],
            ["GB 123456789 0", False, ["Invalid UK EORI number"]],
            ["XI 123456789 0", False, ["Invalid UK EORI number"]],
            ["GB ABCD12345 0", False, ["Invalid UK EORI number"]],
            ["XI ABCD12345 0", False, ["Invalid UK EORI number"]],
            ["GB 12345*&-/ 0", False, ["Invalid UK EORI number"]],
            ["XI 12345*&-/ 0", False, ["Invalid UK EORI number"]],
            ["123456789", False, ["Invalid UK EORI number"]],
            ["123456789000", False, ["Invalid UK EORI number"]],
            ["123456789000123", False, ["Invalid UK EORI number"]],
            ["GBGBGBGBGB", False, ["Invalid UK EORI number"]],
            ["XIXIXIXIXI", False, ["Invalid UK EORI number"]],
        ]
    )
    def test_eori_number_validity(self, eori, is_valid, errors):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        data = {
            "name": "regional site",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": eori,
            "sic_number": self.faker.sic_number(),
            "vat_number": self.faker.vat_number(),
            "registration_number": self.faker.registration_number(),
            "phone_number": "+441234567999",
            "website": "",
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

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK if is_valid else status.HTTP_400_BAD_REQUEST)
        if not is_valid:
            self.assertEqual(
                response.json()["errors"]["eori_number"],
                errors,
            )

    def test_edit_organisation_details(self):
        organisation = OrganisationFactory(type=OrganisationType.COMMERCIAL)
        self.gov_user.role.permissions.set(
            [GovPermissions.MANAGE_ORGANISATIONS.name, GovPermissions.REOPEN_CLOSED_CASES.name]
        )

        data = {
            "name": "regional site",
            "type": OrganisationType.COMMERCIAL,
            "eori_number": "GB123456789000",
            "sic_number": self.faker.sic_number(),
            "vat_number": self.faker.vat_number(),
            "registration_number": self.faker.registration_number(),
            "phone_number": "+441234567999",
            "website": "",
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

        response = self.client.put(self._get_url(organisation.id), data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self._get_url(organisation.id), data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        site = response["primary_site"]
        self.assertEqual(response["name"], data["name"])
        self.assertEqual(response["phone_number"], data["phone_number"])
        self.assertEqual(site["name"], data["site"]["name"])
        self.assertEqual(site["address"]["address_line_1"], data["site"]["address"]["address_line_1"])
        self.assertEqual(site["address"]["postcode"], data["site"]["address"]["postcode"])


class EditOrganisationStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory(status=OrganisationStatus.IN_REVIEW)
        UserOrganisationRelationshipFactory(organisation=self.organisation, user=self.exporter_user)
        self.url = reverse("organisations:organisation_status", kwargs={"pk": self.organisation.pk})

    @mock.patch("api.organisations.notify.notify_exporter_organisation_approved")
    def test_set_organisation_status_active_success(self, mocked_notify):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])
        data = {"status": OrganisationStatus.ACTIVE}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"]["key"], OrganisationStatus.ACTIVE)
        self.assertEqual(Audit.objects.count(), 1)
        mocked_notify.assert_called_with(self.organisation)

    @mock.patch("api.organisations.notify.notify_exporter_organisation_rejected")
    def test_set_organisation_status_rejected_success(self, mocked_notify):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])
        data = {"status": OrganisationStatus.REJECTED}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"]["key"], OrganisationStatus.REJECTED)
        self.assertEqual(Audit.objects.count(), 1)
        mocked_notify.assert_called_with(self.organisation)

    def test_set_organisation_status__without_permission_failure(self):
        data = {"status": OrganisationStatus.ACTIVE}

        response = self.client.put(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Audit.objects.count(), 0)


class UpdateOrganisationDraftTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory(status=OrganisationStatus.DRAFT)
        UserOrganisationRelationshipFactory(organisation=self.organisation, user=self.exporter_user)
        self.exporter_headers["HTTP_ORGANISATION_ID"] = str(self.organisation.id)
        self.url = reverse("organisations:organisation_draft_update", kwargs={"pk": self.organisation.pk})

    def test_update_organisation_status_success(self):
        data = {"name": "Lite Corp"}
        response = self.client.put(self.url, data, **self.exporter_headers)
        self.organisation.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["organisation"]["name"], data["name"])
        self.assertEqual(self.organisation.name, data["name"])

    def test_update_organisation_non_draft_fails(self):
        self.organisation.status = OrganisationStatus.ACTIVE
        self.organisation.save()
        data = {"name": "Lite Corp"}
        response = self.client.put(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["errors"], {"error": "Organisation is not activated or not in draft"})

    def test_update_organisation_fails_validation_errors(self):
        data = {"vat_number": "xyz"}
        response = self.client.put(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"vat_number": ["Standard UK VAT numbers are 9 digits long"]})


class ValidateRegistrationNumberTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory()
        UserOrganisationRelationshipFactory(organisation=self.organisation, user=self.exporter_user)
        self.exporter_headers["HTTP_ORGANISATION_ID"] = str(self.organisation.id)
        self.url = reverse("organisations:registration_number")

    def test_validate_registration_number_success(self):
        data = {"registration_number": "123456789"}
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), data)

    def test_validate_registration_number_fail(self):
        self.organisation.refresh_from_db()
        data = {"registration_number": self.organisation.registration_number}
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(), {"errors": {"registration_number": ["This registration number is already in use."]}}
        )

    @parameterized.expand([OrganisationStatus.REJECTED, OrganisationStatus.DRAFT])
    def test_validate_registration_number_success_for_rejected_or_draft_org(self, org_status):
        self.organisation.refresh_from_db()
        self.organisation.status = org_status
        self.organisation.save()
        data = {"registration_number": self.organisation.registration_number}
        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), data)
