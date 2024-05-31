from django.forms import model_to_dict
from django.utils import timezone

from test_helpers.clients import DataTestClient

from api.appeals.tests.factories import AppealFactory
from api.cases.models import CaseType, Queue
from api.flags.models import Flag
from api.applications.models import (
    ApplicationDocument,
    ExternalLocationOnApplication,
    GoodOnApplication,
    GoodOnApplicationDocument,
    GoodOnApplicationInternalDocument,
    PartyOnApplication,
    SiteOnApplication,
)
from api.applications.tests.factories import (
    ApplicationDocumentFactory,
    ExternalLocationOnApplicationFactory,
    SiteOnApplicationFactory,
    StandardApplicationFactory,
    GoodOnApplicationDocumentFactory,
    GoodOnApplicationInternalDocumentFactory,
    GoodOnApplicationFactory,
    PartyOnApplicationFactory,
)
from api.users.models import GovUser, ExporterUser
from api.goods.tests.factories import FirearmFactory
from api.organisations.tests.factories import OrganisationFactory
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.report_summaries.models import ReportSummary, ReportSummaryPrefix, ReportSummarySubject
from api.staticdata.statuses.models import CaseStatus, CaseSubStatus


class TestStandardApplication(DataTestClient):

    def test_clone(self):
        original_application = StandardApplicationFactory(
            activity="Trade",
            agreed_to_foi=True,
            amendment_of=StandardApplicationFactory(),
            appeal=AppealFactory(),
            appeal_deadline=timezone.now(),
            case_officer=GovUser.objects.first(),
            case_type=CaseType.objects.get(reference="siel"),
            clearance_level="5",
            compliant_limitations_eu_ref="some ref",
            copy_of=StandardApplicationFactory(),
            export_type="permanent",
            f1686_approval_date=timezone.now(),
            f1686_contracting_authority="some authority",
            f1686_reference_number="some ref",
            f680_reference_number="some ref",
            foi_reason="some foi reason",
            goods_recipients="some recipients",
            goods_starting_point="some start",
            have_you_been_informed="yes",
            informed_wmd_ref="some ref",
            intended_end_use="this is our intended end use",
            is_compliant_limitations_eu=True,
            is_eu_military=True,
            is_informed_wmd=True,
            is_military_end_use_controls=True,
            is_mod_security_approved=True,
            is_shipped_waybill_or_lading=True,
            is_suspected_wmd=False,
            is_temp_direct_control=True,
            last_closed_at=timezone.now(),
            military_end_use_controls_ref="some ref",
            name="Application Test Name",
            non_waybill_or_lading_route_details="some details",
            organisation=OrganisationFactory(),
            other_security_approval_details="some details",
            proposed_return_date=timezone.now(),
            reference_number_on_information_form="some ref",
            security_approvals=["some approvals"],
            sla_days=10,
            sla_remaining_days=20,
            sla_updated_at=timezone.now(),
            status=CaseStatus.objects.get(status="ogd_advice"),
            sub_status=CaseSubStatus.objects.first(),
            submitted_at=timezone.now(),
            submitted_by=ExporterUser.objects.first(),
            suspected_wmd_ref="some ref",
            temp_direct_control_details="some details",
            temp_export_details="some details",
            trade_control_activity="some activity",
            trade_control_activity_other="some other activity",
            trade_control_product_categories=["some categories"],
            usage="Trade",
        )
        original_application.flags.add(Flag.objects.first())
        original_application.queues.add(Queue.objects.first())
        original_application.save()
        original_application_document = ApplicationDocumentFactory(application=original_application)
        original_site_on_application = SiteOnApplicationFactory(application=original_application)
        original_external_location_on_application = ExternalLocationOnApplicationFactory(
            application=original_application
        )
        original_good_on_application = GoodOnApplicationFactory(application=original_application)
        original_party_on_application = PartyOnApplicationFactory(application=original_application)
        cloned_application = original_application.clone()

        assert cloned_application.id != original_application.id
        assert model_to_dict(cloned_application) == {
            "activity": "Trade",
            "additional_contacts": [],
            "agreed_to_foi": True,
            "amendment_of": None,
            "appeal": None,
            "appeal_deadline": None,
            "baseapplication_ptr": cloned_application.baseapplication_ptr_id,
            "case_officer": None,
            "case_ptr": cloned_application.case_ptr_id,
            "case_type": original_application.case_type.id,
            "clearance_level": "5",
            "compliant_limitations_eu_ref": "some ref",
            "copy_of": None,
            "export_type": "permanent",
            "f1686_approval_date": original_application.f1686_approval_date,
            "f1686_contracting_authority": "some authority",
            "f1686_reference_number": "some ref",
            "f680_reference_number": "some ref",
            "flags": [],
            "foi_reason": "some foi reason",
            "goods_recipients": "some recipients",
            "goods_starting_point": "some start",
            "have_you_been_informed": "yes",
            "informed_wmd_ref": "some ref",
            "intended_end_use": "this is our intended end use",
            "is_compliant_limitations_eu": True,
            "is_eu_military": True,
            "is_informed_wmd": True,
            "is_military_end_use_controls": True,
            "is_mod_security_approved": True,
            "is_shipped_waybill_or_lading": True,
            "is_suspected_wmd": False,
            "is_temp_direct_control": True,
            "last_closed_at": None,
            "military_end_use_controls_ref": "some ref",
            "name": "Application Test Name",
            "non_waybill_or_lading_route_details": "some details",
            "organisation": original_application.organisation_id,
            "other_security_approval_details": "some details",
            "proposed_return_date": original_application.proposed_return_date,
            "queues": [],
            "reference_number_on_information_form": "some ref",
            "security_approvals": ["some approvals"],
            "sla_days": 0,
            "sla_remaining_days": None,
            "sla_updated_at": None,
            "status": CaseStatus.objects.get(status="draft").id,
            "sub_status": None,
            "submitted_at": None,
            "submitted_by": None,
            "suspected_wmd_ref": "some ref",
            "temp_direct_control_details": "some details",
            "temp_export_details": "some details",
            "trade_control_activity": "some activity",
            "trade_control_activity_other": "some other activity",
            "trade_control_product_categories": ["some categories"],
            "usage": "Trade",
        }
        # Defer testing of related models' cloning to more specific unit tests
        assert ApplicationDocument.objects.filter(application=cloned_application).count() == 1
        assert SiteOnApplication.objects.filter(application=cloned_application).count() == 1
        assert ExternalLocationOnApplication.objects.filter(application=cloned_application).count() == 1
        assert GoodOnApplication.objects.filter(application=cloned_application).count() == 1
        assert PartyOnApplication.objects.filter(application=cloned_application).count() == 1


class TestApplicationDocument(DataTestClient):

    def test_clone(self):
        original_application_document = ApplicationDocumentFactory.create(
            description="some doc description",
            document_type="type",
            name="some doc name",
            s3_key="some.doc",
            safe=True,
            size=100,
            virus_scanned_at=timezone.now(),
        )
        new_application = StandardApplicationFactory()
        cloned_application_document = original_application_document.clone(
            application=new_application,
        )
        assert cloned_application_document.application_id != original_application_document.application_id
        assert cloned_application_document.document_ptr_id != original_application_document.document_ptr_id
        assert model_to_dict(cloned_application_document) == {
            "application": new_application.id,
            "description": original_application_document.description,
            "document_ptr": cloned_application_document.document_ptr_id,
            "document_type": original_application_document.document_type,
            "name": original_application_document.name,
            "s3_key": original_application_document.s3_key,
            "safe": original_application_document.safe,
            "size": original_application_document.size,
            "virus_scanned_at": original_application_document.virus_scanned_at,
        }


class TestSiteOnApplication(DataTestClient):

    def test_clone(self):
        original_site_on_application = SiteOnApplicationFactory()
        new_application = StandardApplicationFactory()
        cloned_site_on_application = original_site_on_application.clone(application=new_application)
        assert cloned_site_on_application.application_id != original_site_on_application.application_id
        assert model_to_dict(cloned_site_on_application) == {
            "application": new_application.id,
            "site": original_site_on_application.site.id,
        }


class TestExternalLocationOnApplication(DataTestClient):

    def test_clone(self):
        original_external_location_on_application = ExternalLocationOnApplicationFactory()
        new_application = StandardApplicationFactory()
        cloned_external_location_on_application = original_external_location_on_application.clone(
            application=new_application
        )
        assert cloned_external_location_on_application.id != original_external_location_on_application.id
        assert cloned_external_location_on_application.application_id != original_external_location_on_application.id
        assert model_to_dict(cloned_external_location_on_application) == {
            "application": new_application.id,
            "external_location": original_external_location_on_application.external_location_id,
        }


class TestGoodOnApplication(DataTestClient):

    def test_clone(self):
        original_good_on_application = GoodOnApplicationFactory(
            firearm_details=FirearmFactory(),
            assessed_by=GovUser.objects.first(),
            assessment_date=timezone.now(),
            comment="some assessment comment",
            control_list_entries=[ControlListEntry.objects.get(rating="ML1")],
            end_use_control=["some control"],
            is_good_controlled=True,
            is_good_incorporated=False,
            is_nca_applicable=True,
            is_ncsc_military_information_security=True,
            is_onward_altered_processed=False,
            is_onward_altered_processed_comments="some comment",
            is_onward_exported=True,
            is_onward_incorporated=True,
            is_onward_incorporated_comments="some comment",
            is_precedent=False,
            is_trigger_list_guidelines_applicable=False,
            item_type="some type",
            nsg_assessment_note="some assessment note",
            nsg_list_type="some list type",
            other_item_type="type",
            quantity=10,
            regime_entries=["M1A2"],
            report_summaries=[ReportSummary.objects.first()],
            report_summary="some report summary",
            report_summary_prefix=ReportSummaryPrefix.objects.first(),
            report_summary_subject=ReportSummarySubject.objects.first(),
            unit="MIM",
            value=200,
        )
        original_good_on_application_internal_document = GoodOnApplicationInternalDocumentFactory(
            document_title="some title",
            name="some name",
            s3_key="doc.xlsx",
            safe=True,
            size=100,
            good_on_application=original_good_on_application,
        )
        original_good_on_application_document = GoodOnApplicationDocumentFactory(
            document_type="some type",
            name="some name",
            s3_key="doc.xlsx",
            safe=True,
            size=100,
            good_on_application=original_good_on_application,
            good=original_good_on_application.good,
            application=original_good_on_application.application,
        )

        new_application = StandardApplicationFactory()
        cloned_good_on_application = original_good_on_application.clone(application=new_application)
        assert cloned_good_on_application.id != original_good_on_application.id
        assert cloned_good_on_application.firearm_details_id != original_good_on_application.firearm_details_id
        assert model_to_dict(cloned_good_on_application) == {
            "application": new_application.id,
            "assessed_by": None,
            "assessment_date": None,
            "comment": None,
            "control_list_entries": [],
            "end_use_control": ["some control"],
            "firearm_details": cloned_good_on_application.firearm_details_id,
            "good": original_good_on_application.good_id,
            "is_good_controlled": None,
            "is_good_incorporated": False,
            "is_nca_applicable": True,
            "is_ncsc_military_information_security": True,
            "is_onward_altered_processed": False,
            "is_onward_altered_processed_comments": "some comment",
            "is_onward_exported": True,
            "is_onward_incorporated": True,
            "is_onward_incorporated_comments": "some comment",
            "is_precedent": False,
            "is_trigger_list_guidelines_applicable": None,
            "item_type": "some type",
            "nsg_assessment_note": "",
            "nsg_list_type": "",
            "other_item_type": "type",
            "quantity": 10,
            "regime_entries": [],
            "report_summaries": [],
            "report_summary": None,
            "report_summary_prefix": None,
            "report_summary_subject": None,
            "unit": "MIM",
            "value": 200,
        }
        # Defer checking of related models' clone() methods to specific unit tests
        assert (
            GoodOnApplicationInternalDocument.objects.filter(good_on_application=cloned_good_on_application).count()
            == 1
        )
        assert GoodOnApplicationDocument.objects.filter(good_on_application=cloned_good_on_application).count() == 1


class TestGoodOnApplicationDocument(DataTestClient):

    def test_clone(self):
        original_good_on_application_document = GoodOnApplicationDocumentFactory(
            document_type="some type",
            name="some name",
            s3_key="doc.xlsx",
            safe=True,
            size=100,
        )
        new_application = StandardApplicationFactory()
        new_good_on_application = GoodOnApplicationFactory()
        cloned_good_on_application_document = original_good_on_application_document.clone(
            application=new_application, good_on_application=new_good_on_application
        )
        assert cloned_good_on_application_document.id != original_good_on_application_document.id
        assert (
            cloned_good_on_application_document.application_id != original_good_on_application_document.application_id
        )
        assert model_to_dict(cloned_good_on_application_document) == {
            "application": new_application.id,
            "document_ptr": cloned_good_on_application_document.document_ptr_id,
            "document_type": "some type",
            "good": original_good_on_application_document.good_id,
            "good_on_application": new_good_on_application.id,
            "name": "some name",
            "s3_key": "doc.xlsx",
            "safe": True,
            "size": 100,
            "user": original_good_on_application_document.user_id,
            "virus_scanned_at": original_good_on_application_document.virus_scanned_at,
        }


class TestGoodOnApplicationInternalDocument(DataTestClient):

    def test_clone(self):
        original_good_on_application_internal_document = GoodOnApplicationInternalDocumentFactory(
            document_title="some title",
            name="some name",
            s3_key="doc.xlsx",
            safe=True,
            size=100,
        )
        new_good_on_application = GoodOnApplicationFactory()
        cloned_good_on_application_internal_document = original_good_on_application_internal_document.clone(
            good_on_application=new_good_on_application
        )
        assert cloned_good_on_application_internal_document.id != original_good_on_application_internal_document.id
        assert model_to_dict(cloned_good_on_application_internal_document) == {
            "document_ptr": cloned_good_on_application_internal_document.document_ptr_id,
            "good_on_application": new_good_on_application.id,
            "document_title": "some title",
            "name": "some name",
            "s3_key": "doc.xlsx",
            "safe": True,
            "size": 100,
            "virus_scanned_at": original_good_on_application_internal_document.virus_scanned_at,
        }


class TestPartyOnApplication(DataTestClient):

    def test_clone(self):
        original_party_on_application = PartyOnApplicationFactory(
            deleted_at=timezone.now(),
        )
        original_party_on_application.flags.add(Flag.objects.first())
        original_party_on_application.save()
        new_application = StandardApplicationFactory()
        cloned_party_on_application = original_party_on_application.clone(application=new_application)
        assert cloned_party_on_application.id != original_party_on_application.id
        assert cloned_party_on_application.application_id == new_application.id
        assert model_to_dict(cloned_party_on_application) == {
            "id": cloned_party_on_application.id,
            "application": new_application.id,
            "deleted_at": original_party_on_application.deleted_at,
            "flags": [],
            "party": original_party_on_application.party_id,
        }
