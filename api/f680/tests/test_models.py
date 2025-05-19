import pytest
from unittest import mock

from django.forms import model_to_dict

from .factories import F680ApplicationFactory, SubmittedF680ApplicationFactory
from api.users.tests.factories import ExporterUserFactory
from api.f680.models import Product, SecurityReleaseRequest
from api.f680.exporter.serializers import SubmittedApplicationJSONSerializer
from api.cases.enums import AdviceType, CaseTypeEnum
from api.applications.exceptions import AmendmentError
from api.staticdata.statuses.enums import CaseStatusIdEnum
from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from lite_routing.routing_rules_internal.enums import TeamIdEnum


pytestmark = pytest.mark.django_db

pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


class TestF680Application:

    def test_on_submit_fields_present_in_application_json(
        self, data_application_json, data_australia_release_id, data_france_release_id, data_uae_release_id
    ):
        f680_application = F680ApplicationFactory(application=data_application_json)
        assert f680_application.name is None
        serializer = SubmittedApplicationJSONSerializer(data=f680_application.application)
        serializer.is_valid(raise_exception=True)
        f680_application.submitted_by = ExporterUserFactory()
        f680_application.on_submit(f680_application.status.status, serializer.data)
        f680_application.refresh_from_db()
        assert f680_application.name == "some name"

        assert Product.objects.all().count() == 1
        product = Product.objects.first()
        assert product.name == "some product name"
        assert product.description == "some product description"
        assert product.security_grading == "official"
        assert product.security_grading_other == "some other grading"
        assert product.organisation == f680_application.organisation

        expected_security_release_count = len(data_application_json["sections"]["user_information"]["items"])
        assert f680_application.security_release_requests.all().count() == expected_security_release_count

        australia_release = SecurityReleaseRequest.objects.get(id=data_australia_release_id)
        australia_recipient = australia_release.recipient
        assert australia_recipient.name == "australia name"
        assert australia_recipient.address == "australia address"
        assert australia_recipient.country_id == "AU"
        assert australia_recipient.type == "third-party"
        assert australia_recipient.organisation == f680_application.organisation
        assert australia_recipient.role == "consultant"
        assert australia_release.product == product
        assert australia_release.security_grading == "secret"
        assert australia_release.intended_use == "australia intended use"

        france_release = SecurityReleaseRequest.objects.get(id=data_france_release_id)
        france_recipient = france_release.recipient
        assert france_recipient.name == "france name"
        assert france_recipient.address == "france address"
        assert france_recipient.country_id == "FR"
        assert france_recipient.type == "ultimate-end-user"
        assert france_recipient.organisation == f680_application.organisation
        assert france_release.product == product
        assert france_release.security_grading == "official"
        assert france_release.security_grading_other == "some other grading"
        assert france_release.intended_use == "france intended use"

        uae_release = SecurityReleaseRequest.objects.get(id=data_uae_release_id)
        uae_recipient = uae_release.recipient
        assert uae_recipient.name == "uae name"
        assert uae_recipient.address == "uae address"
        assert uae_recipient.country_id == "AE"
        assert uae_recipient.type == "end-user"
        assert uae_recipient.organisation == f680_application.organisation
        assert uae_release.product == product
        assert uae_release.security_grading == "top-secret"
        assert uae_release.intended_use == "uae intended use"

    def test_on_submit_name_missing_in_application_json(self):
        f680_application = F680ApplicationFactory()
        assert f680_application.name is None
        with pytest.raises(KeyError):
            f680_application.on_submit(f680_application.status.status, {})

    def test_clone_application(self, data_application_json):
        f680_application = F680ApplicationFactory(
            name="F680_APP_1",
            status_id=CaseStatusIdEnum.REOPENED_FOR_CHANGES,
            sla_days=14,
            application=data_application_json,
        )
        cloned_application = f680_application.clone(amendment_of=f680_application)
        cloned_application_data = model_to_dict(cloned_application)

        new_application_json = cloned_application_data.pop("application")
        assert new_application_json != f680_application.application

        # Remove items from application json to prove the difference lies in this section
        f680_items = f680_application.application["sections"]["user_information"].pop("items")
        new_f680_items = new_application_json["sections"]["user_information"].pop("items")
        assert new_application_json == f680_application.application

        # Remove the ids from items and assert they are different (so have therefore been updated)
        assert [item.pop("id") for item in new_f680_items] != [item.pop("id") for item in f680_items]

        # Assert the remaining items data is the same
        assert new_f680_items == f680_items

        assert cloned_application_data == {
            "activity": None,
            "additional_contacts": [],
            "agreed_to_foi": None,
            "amendment_of": f680_application.pk,
            "appeal": None,
            "appeal_deadline": None,
            "baseapplication_ptr": cloned_application.pk,
            "case_officer": None,
            "case_ptr": cloned_application.pk,
            "case_type": CaseTypeEnum.F680.id,
            "clearance_level": None,
            "compliant_limitations_eu_ref": None,
            "copy_of": None,
            "flags": [],
            "foi_reason": "",
            "informed_wmd_ref": None,
            "intended_end_use": None,
            "is_compliant_limitations_eu": None,
            "is_eu_military": None,
            "is_informed_wmd": None,
            "is_military_end_use_controls": None,
            "is_suspected_wmd": None,
            "last_closed_at": None,
            "military_end_use_controls_ref": None,
            "name": "F680_APP_1",
            "organisation": f680_application.organisation.pk,
            "queues": [],
            "sla_days": 0,
            "sla_remaining_days": None,
            "sla_updated_at": None,
            "status": CaseStatusIdEnum.DRAFT,
            "sub_status": None,
            "submitted_at": None,
            "submitted_by": None,
            "suspected_wmd_ref": None,
            "usage": None,
        }

    def test_create_amendment(self, data_application_json):
        exporter_user = ExporterUserFactory()
        f680_application = SubmittedF680ApplicationFactory(
            name="F680_APP_1",
            application=data_application_json,
        )
        assert f680_application.status_id == CaseStatusIdEnum.SUBMITTED
        new_f680_application = f680_application.create_amendment(exporter_user)
        f680_application.refresh_from_db()
        assert f680_application.status_id == CaseStatusIdEnum.SUPERSEDED_BY_EXPORTER_EDIT
        assert new_f680_application.status_id == CaseStatusIdEnum.DRAFT
        assert new_f680_application.name == f680_application.name
        assert new_f680_application.amendment_of == f680_application
        assert Audit.objects.filter(target_object_id=f680_application.get_case().id).count() == 2
        assert Audit.objects.filter(target_object_id=new_f680_application.get_case().id).count() == 1

    def test_create_amendment_error(self, data_application_json):
        exporter_user = ExporterUserFactory()
        f680_application = F680ApplicationFactory(
            name="F680_APP_1",
            application=data_application_json,
        )
        assert f680_application.status_id == CaseStatusIdEnum.DRAFT
        with pytest.raises(AmendmentError) as error:
            f680_application.create_amendment(exporter_user)
        assert "Failed to create an amendment from" in str(error.value)

    def test_create_amendment_one_already_exists(self, data_application_json):
        exporter_user = ExporterUserFactory()
        f680_application = F680ApplicationFactory(
            name="F680_APP_1",
            application=data_application_json,
        )
        submitted_f680_application = SubmittedF680ApplicationFactory(amendment_of=f680_application)
        assert f680_application.status_id == CaseStatusIdEnum.DRAFT
        result = f680_application.create_amendment(exporter_user)
        assert result == submitted_f680_application

    @mock.patch("api.cases.notify.notify_exporter_f680_outcome_issued")
    def test_finalise_application(self, mock_notify, data_application_json, team_case_advisor):
        gov_user = team_case_advisor(TeamIdEnum.MOD_ECJU)
        f680_application = F680ApplicationFactory(
            name="F680_APP_1",
            application=data_application_json,
            status_id=CaseStatusIdEnum.UNDER_REVIEW,
            submitted_by=ExporterUserFactory(),
        )
        response = f680_application.finalise(gov_user, {AdviceType.APPROVE, AdviceType.REFUSE}, "Note")
        assert response == ""
        audit_trail = Audit.objects.filter(target_object_id=f680_application.get_case().id)
        assert list(audit_trail.values_list("verb", flat=True)) == [
            AuditType.FINALISED_APPLICATION,
            AuditType.UPDATED_SUB_STATUS,
            AuditType.UPDATED_SUB_STATUS,
            AuditType.UPDATED_STATUS,
        ]

        f680_application.refresh_from_db()
        assert f680_application.status_id == CaseStatusIdEnum.FINALISED
        assert f680_application.sub_status.name == "Approved"
        mock_notify.assert_called_with(f680_application)
        assert mock_notify.call_count == 1

    @mock.patch("api.cases.notify.notify_exporter_f680_outcome_issued")
    def test_finalise_already_finalised_application(self, mock_notify, data_application_json, team_case_advisor):
        gov_user = team_case_advisor(TeamIdEnum.MOD_ECJU)
        f680_application = F680ApplicationFactory(
            name="F680_APP_1",
            application=data_application_json,
            status_id=CaseStatusIdEnum.FINALISED,
            submitted_by=ExporterUserFactory(),
        )
        response = f680_application.finalise(gov_user, {AdviceType.APPROVE}, "Note")
        assert response == ""
        assert not Audit.objects.filter(target_object_id=f680_application.get_case().id).exists()
        assert mock_notify.call_count == 0
