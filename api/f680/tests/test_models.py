import pytest

from .factories import F680ApplicationFactory, SubmittedF680ApplicationFactory
from api.users.tests.factories import ExporterUserFactory

from api.f680.models import Product, SecurityReleaseRequest
from api.f680.exporter.serializers import SubmittedApplicationJSONSerializer

from api.applications.exceptions import AmendmentError
from api.staticdata.statuses.enums import CaseStatusIdEnum
from api.audit_trail.models import Audit

pytestmark = pytest.mark.django_db


class TestF680Application:

    def test_on_submit_fields_present_in_application_json(
        self, data_application_json, data_australia_release_id, data_france_release_id, data_uae_release_id
    ):
        f680_application = F680ApplicationFactory(application=data_application_json)
        assert f680_application.name is None
        serializer = SubmittedApplicationJSONSerializer(data=f680_application.application)
        serializer.is_valid(raise_exception=True)
        f680_application.on_submit(serializer.data)
        f680_application.refresh_from_db()
        assert f680_application.name == "some name"

        assert Product.objects.all().count() == 1
        product = Product.objects.first()
        assert product.name == "some product name"
        assert product.description == "some product description"
        assert product.security_grading == "official"
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
            f680_application.on_submit({})

    def test_clone_application(self, data_application_json):
        f680_application = F680ApplicationFactory(
            name="F680_APP_1",
            status_id=CaseStatusIdEnum.REOPENED_FOR_CHANGES,
            sla_days=14,
            application=data_application_json,
        )
        new_f680_application = f680_application.clone(amendment_of=f680_application)
        assert new_f680_application.name == f680_application.name
        assert new_f680_application.amendment_of == f680_application
        assert new_f680_application.status_id == CaseStatusIdEnum.DRAFT
        assert new_f680_application.sla_days == 0
        assert new_f680_application.organisation == f680_application.organisation

        assert new_f680_application.application != f680_application.application

        # Remove items from application json to prove the difference lies in this section
        f680_items = f680_application.application["sections"]["user_information"].pop("items")
        new_f680_items = new_f680_application.application["sections"]["user_information"].pop("items")
        assert new_f680_application.application == f680_application.application

        # Remove the ids from items and assert they are different (so have therefore been updated)
        assert [item.pop("id") for item in new_f680_items] != [item.pop("id") for item in f680_items]

        # Assert the remaining items data is the same
        assert f680_items == new_f680_items

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
