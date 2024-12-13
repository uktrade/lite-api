from unittest import mock
from django.urls import reverse
from rest_framework import status
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from api.core.constants import Roles
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.teams.enums import TeamIdEnum
from api.teams.models import Team
from api.users.models import Role
from parameterized import parameterized
from reversion.models import Version

from api.applications.tests.factories import StandardApplicationFactory
from api.cases.enums import CaseTypeEnum, AdviceType
from api.cases.tests.factories import FinalAdviceFactory
from api.licences.enums import LicenceStatus
from api.licences.tests.factories import GoodOnLicenceFactory
from api.licences.views.main import LicenceType
from api.licences.tests.factories import StandardLicenceFactory
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.countries.models import Country
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from test_helpers.helpers import node_by_id


class GetLicencesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("licences:licences")
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.applications = [self.standard_application]
        self.template = self.create_letter_template(case_types=[CaseTypeEnum.SIEL.id])
        self.documents = [
            self.create_generated_case_document(application, self.template, advice_type=AdviceType.APPROVE)
            for application in self.applications
        ]
        self.licences = {
            application: StandardLicenceFactory(case=application, status=LicenceStatus.ISSUED)
            for application in self.applications
        }

        for application, licence in self.licences.items():
            for good in application.goods.all():
                good.control_list_entries.add(ControlListEntry.objects.get(rating="ML2b"))
                FinalAdviceFactory(user=self.gov_user, good=good.good, case=application)
                GoodOnLicenceFactory(licence=licence, good=good, quantity=good.quantity, value=good.value)

    def test_get_all_licences(self):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]
        response_data.reverse()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(self.applications))
        for i in range(len(self.applications)):
            licence = response_data[i]
            licence_object = list(self.licences.values())[i]
            self.assertEqual(licence["id"], str(licence_object.id))
            self.assertEqual(licence["application"]["id"], str(self.applications[i].id))
            self.assertEqual(licence["reference_code"], licence_object.reference_code)
            self.assertEqual(licence["status"]["key"], licence_object.status)
            self.assertEqual(licence["application"]["documents"][0]["id"], str(self.documents[i].id))
        # Assert correct information is returned
        for licence in self.licences.values():
            licence_data = node_by_id(response_data, licence.id)

            for goods_data, good_on_licence in zip(licence_data["goods"], licence.goods.all()):
                good_on_application = good_on_licence.good
                good = good_on_application.good
                self.assertEqual(
                    goods_data,
                    {
                        "id": str(good_on_licence.pk),
                        "assessed_control_list_entries": [
                            {
                                "id": str(cle.pk),
                                "rating": cle.rating,
                                "text": cle.text,
                            }
                            for cle in good_on_application.control_list_entries.all()
                        ],
                        "control_list_entries": [
                            {
                                "id": str(cle.pk),
                                "rating": cle.rating,
                                "text": cle.text,
                            }
                            for cle in good.control_list_entries.all()
                        ],
                        "description": good.description,
                        "good_on_application_id": str(good_on_application.pk),
                        "name": good.name,
                    },
                )

    def test_get_standard_licences_only(self):
        response = self.client.get(self.url + "?licence_type=" + LicenceType.LICENCE, **self.exporter_headers)
        response_data = response.json()["results"]
        ids = [licence["id"] for licence in response_data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertTrue(str(self.licences[self.standard_application].id) in ids)

    def test_draft_licences_are_not_included(self):
        draft_licence = StandardLicenceFactory(case=self.standard_application, status=LicenceStatus.DRAFT)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(str(draft_licence.id) not in [licence["id"] for licence in response_data])


class GetLicencesFilterTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("licences:licences")
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.standard_application_licence = StandardLicenceFactory(
            case=self.standard_application, status=LicenceStatus.ISSUED
        )

    def test_only_my_organisations_licences_are_returned(self):
        self.standard_application.organisation = self.create_organisation_with_exporter_user()[0]
        self.standard_application.save()

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # application is not finalised yet
        self.assertEqual(len(response_data), 0)

    def test_draft_licences_ignored(self):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_application_name(self):
        response = self.client.get(self.url + "?reference=" + self.standard_application.name, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_ecju_reference(self):
        response = self.client.get(
            self.url + "?reference=" + self.standard_application.reference_code, **self.exporter_headers
        )
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_control_list_entry(self):
        response = self.client.get(self.url + "?clc=ML1a", **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertIn(str(self.standard_application_licence.id), response_data[0]["id"])

    def test_filter_by_country_standard_application(self):
        country = Country.objects.first()
        end_user = self.standard_application.end_user.party
        end_user.country = country
        end_user.save()

        response = self.client.get(self.url + "?country=" + str(country.id), **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_end_user_standard_application(self):
        end_user_name = self.standard_application.end_user.party.name

        response = self.client.get(self.url + "?end_user=" + end_user_name, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_active_only(self):
        self.standard_application.status = CaseStatus.objects.get(status=CaseStatusEnum.SURRENDERED)
        self.standard_application.save()

        response = self.client.get(self.url + "?active_only=True", **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 0)


class LicenceDetailsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.status_data = {"status": LicenceStatus.REVOKED}
        self.standard_application = StandardApplicationFactory()
        self.standard_application.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.standard_application.save()

        self.standard_application_licence = StandardLicenceFactory(
            case=self.standard_application, status=LicenceStatus.ISSUED
        )
        self.url = reverse("licences:licence_details", kwargs={"pk": self.standard_application_licence.id})

        # Make User LU Super User
        self.gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        lu_role, _ = Role.objects.get_or_create(
            id=Roles.INTERNAL_LU_SENIOR_MANAGER_ROLE_ID, name=Roles.INTERNAL_LU_SENIOR_MANAGER_ROLE_NAME
        )
        self.gov_user.role = lu_role
        self.gov_user.save()

    def test_get_licence_details(self):

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        assert response.status_code == status.HTTP_200_OK

        expected_data = {
            "id": str(self.standard_application_licence.id),
            "reference_code": self.standard_application_licence.reference_code,
            "status": self.standard_application_licence.status,
            "case_status": self.standard_application_licence.case.status.status,
        }
        assert response_data == expected_data

    def test_get_licence_details_exporter_not_allowed(self):

        response = self.client.get(self.url, **self.exporter_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @parameterized.expand(
        [
            [{"status": "suspended"}, "suspend"],
            [{"status": "reinstated"}, "reinstate"],
        ]
    )
    def test_update_licence_details_message_success(self, data, expect_model_method):

        with mock.patch(f"api.licences.models.Licence.{expect_model_method}") as save_method_mock:

            response = self.client.patch(self.url, data, **self.gov_headers)

            response_data = response.json()
            self.standard_application_licence.refresh_from_db()
            expected_data = {
                "id": str(self.standard_application_licence.id),
                "reference_code": self.standard_application_licence.reference_code,
                "case_status": self.standard_application_licence.case.status.status,
                **data,
            }
            save_method_mock.assert_called_once()
            save_method_mock.assert_called_once_with(self.standard_application_licence, self.gov_user.baseuser_ptr)
            assert response.status_code == status.HTTP_200_OK
            assert response_data == expected_data

    def test_update_licence_details_revoked_success_send_hmrc(self):
        data = {"status": "revoked"}
        with mock.patch("api.licences.models.Licence.revoke") as save_method_mock:
            response = self.client.patch(self.url, data, **self.gov_headers)
            response_data = response.json()
            self.standard_application_licence.refresh_from_db()
            expected_data = {
                "id": str(self.standard_application_licence.id),
                "reference_code": self.standard_application_licence.reference_code,
                "case_status": self.standard_application_licence.case.status.status,
                **data,
            }
            save_method_mock.assert_called_once()
            save_method_mock.assert_called_once_with(self.standard_application_licence, self.gov_user.baseuser_ptr)
            assert response.status_code == status.HTTP_200_OK
            assert response_data == expected_data

    @parameterized.expand(
        [
            [{"status": "revoked"}],
            [{"status": "issued"}],
            [{"status": "suspended"}],
        ]
    )
    def test_update_licence_details_put_fails(self, data):
        response = self.client.put(self.url, data, **self.gov_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_licence_details_invalid_status(self):
        data = {"status": "dummy"}
        response = self.client.patch(self.url, data, **self.gov_headers)
        assert response.json()["errors"] == {"status": ['"dummy" is not a valid choice.']}
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response = self.client.put(self.url, data, **self.gov_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @parameterized.expand(
        [
            [{"reference_code": "1234"}],
            [{"duration": "5"}],
            [{"hmrc_integration_sent_at": True}],
        ]
    )
    def test_update_licence_details_not_updated(self, data):

        response = self.client.patch(self.url, data, **self.gov_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_licence_details_non_lu_admin_forbidden(self):

        defult_role, _ = Role.objects.get_or_create(
            id=Roles.INTERNAL_DEFAULT_ROLE_ID, name=Roles.INTERNAL_DEFAULT_ROLE_NAME
        )
        self.gov_user.role = defult_role
        self.gov_user.save()

        response = self.client.patch(self.url, self.status_data, **self.gov_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @parameterized.expand(
        [
            [CaseStatusEnum.FINALISED, status.HTTP_200_OK],
            [CaseStatusEnum.APPEAL_REVIEW, status.HTTP_403_FORBIDDEN],
            [CaseStatusEnum.SUSPENDED, status.HTTP_403_FORBIDDEN],
            [CaseStatusEnum.REVOKED, status.HTTP_403_FORBIDDEN],
            [CaseStatusEnum.INITIAL_CHECKS, status.HTTP_403_FORBIDDEN],
        ]
    )
    def test_update_licence_details_case_non_finialised(self, case_status, expected_status):
        self.standard_application.status = get_case_status_by_status(case_status)
        self.standard_application.save()

        response = self.client.patch(self.url, self.status_data, **self.gov_headers)
        assert response.status_code == expected_status

    @parameterized.expand(
        [
            [LicenceStatus.ISSUED, status.HTTP_200_OK],
            [LicenceStatus.REINSTATED, status.HTTP_200_OK],
            [LicenceStatus.SUSPENDED, status.HTTP_200_OK],
            [LicenceStatus.REVOKED, status.HTTP_403_FORBIDDEN],
            [LicenceStatus.SURRENDERED, status.HTTP_403_FORBIDDEN],
            [LicenceStatus.EXHAUSTED, status.HTTP_403_FORBIDDEN],
            [LicenceStatus.EXPIRED, status.HTTP_403_FORBIDDEN],
            [LicenceStatus.DRAFT, status.HTTP_403_FORBIDDEN],
            [LicenceStatus.CANCELLED, status.HTTP_403_FORBIDDEN],
        ]
    )
    def test_update_licence_details_case_licence_editable_states(self, licence_status, expected_status):
        self.standard_application_licence.status = licence_status
        self.standard_application_licence.save()

        response = self.client.patch(self.url, self.status_data, **self.gov_headers)
        assert response.status_code == expected_status

    def test_update_licence_details_check_version(self):
        data_items = [{"status": "reinstated"}, {"status": "suspended"}, {"status": "revoked"}]

        response = self.client.patch(self.url, data_items[0], **self.gov_headers)
        assert response.status_code == status.HTTP_200_OK
        response = self.client.patch(self.url, data_items[1], **self.gov_headers)
        assert response.status_code == status.HTTP_200_OK
        response = self.client.patch(self.url, data_items[2], **self.gov_headers)
        assert response.status_code == status.HTTP_200_OK

        # returns most recent first
        versions = Version.objects.get_for_object(self.standard_application_licence)
        self.assertEqual(versions.count(), len(data_items))

        for counter, version in enumerate(versions, start=1):
            self.assertEqual(version.revision.user, self.gov_user.baseuser_ptr)
            self.assertEqual(version.field_dict["status"], data_items[3 - counter]["status"])

    @parameterized.expand(
        [
            [LicenceStatus.REINSTATED],
            [LicenceStatus.SUSPENDED],
            [LicenceStatus.REVOKED],
        ]
    )
    def test_update_licence_details_audit_trail(self, licence_status):
        data = {"status": licence_status}

        response = self.client.patch(self.url, data, **self.gov_headers)

        assert response.status_code == status.HTTP_200_OK
        audit = Audit.objects.filter(verb=AuditType.LICENCE_UPDATED_STATUS).first()
        audit_data = AuditSerializer(audit).data
        assert audit_data["user"]["id"] == self.gov_user.pk
        assert (
            audit_data["text"]
            == f"set the licence status of {self.standard_application_licence.reference_code} from {self.standard_application_licence.status} to {licence_status}."
        )
