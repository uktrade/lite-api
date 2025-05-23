import pytest

from datetime import date
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from django.template.loader import render_to_string
from django.utils import timezone
from parameterized import parameterized

from api.applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from api.applications.models import ExternalLocationOnApplication, GoodOnApplication
from api.applications.tests.factories import GoodOnApplicationFactory
from api.f680.caseworker.serializers import SecurityReleaseRequestSerializer
from api.f680.tests.factories import (
    F680SecurityReleaseOutcomeFactory,
    F680SecurityReleaseRequestFactory,
    SubmittedF680ApplicationFactory,
)
from api.cases.enums import AdviceType
from api.licences.tests.factories import StandardLicenceFactory
from api.letter_templates.context_generator import EcjuQuerySerializer
from api.cases.tests.factories import FinalAdviceFactory

from api.core.helpers import add_months, DATE_FORMAT, friendly_boolean, get_value_from_enum
from api.f680.enums import ApprovalTypes
from api.goods.enums import (
    PvGrading,
    MilitaryUse,
    Component,
    ItemCategory,
    GoodControlled,
    GoodPvGraded,
)
from api.goods.tests.factories import GoodFactory, FirearmFactory
from api.cases.tests.factories import CaseAssignmentFactory, EcjuQueryFactory
from api.letter_templates.context_generator import get_document_context
from api.licences.enums import LicenceStatus
from api.licences.tests.factories import GoodOnLicenceFactory
from api.parties.enums import PartyType, SubType
from api.parties.models import Party
from api.queues.models import Queue
from api.staticdata.trade_control.enums import TradeControlActivity, TradeControlProductCategory
from api.staticdata.units.enums import Units
from test_helpers.clients import DataTestClient

from lite_routing.routing_rules_internal.enums import QueuesEnum


@pytest.mark.context_gen
class DocumentContextGenerationTests(DataTestClient):
    def _assert_applicant(self, context, case):
        applicant = case.submitted_by
        self.assertEqual(context["name"], " ".join([applicant.first_name, applicant.last_name]))
        self.assertEqual(context["email"], applicant.email)

    def _assert_addressee(self, context, addressee):
        self.assertEqual(context["name"], addressee.name)
        self.assertEqual(context["email"], addressee.email)
        self.assertEqual(context["phone_number"], addressee.phone_number)
        self.assertEqual(context["address"], addressee.address)

    def _assert_address(self, context, address):
        self.assertEqual(
            context["address_line_1"],
            address.address_line_1 or address.address,
        )
        self.assertEqual(context["address_line_2"], address.address_line_2)
        self.assertEqual(context["postcode"], address.postcode)
        self.assertEqual(context["city"], address.city)
        self.assertEqual(context["region"], address.region)
        self.assertEqual(context["country"]["name"], address.country.name)
        self.assertEqual(context["country"]["code"], address.country.id)

    def _assert_organisation(self, context, organisation):
        self.assertEqual(context["name"], organisation.name)
        self.assertEqual(context["eori_number"], organisation.eori_number)
        self.assertEqual(context["sic_number"], organisation.sic_number)
        self.assertEqual(context["vat_number"], organisation.vat_number)
        self.assertEqual(context["registration_number"], organisation.registration_number)
        self.assertEqual(context["primary_site"]["name"], organisation.primary_site.name)
        self._assert_address(context["primary_site"], organisation.primary_site.address)

    def _assert_licence(self, context, licence):
        self.assertEqual(context["start_date"], licence.start_date.strftime(DATE_FORMAT))
        self.assertEqual(context["duration"], licence.duration)
        self.assertEqual(context["end_date"], add_months(licence.start_date, licence.duration))
        self.assertEqual(context["reference_code"], licence.reference_code)

    def _assert_party(self, context, party):
        self.assertEqual(context["name"], party.name)
        self.assertEqual(context["address"], party.address)
        self.assertEqual(context["country"]["name"], party.country.name)
        self.assertEqual(context["country"]["code"], party.country.id)
        self.assertEqual(context["website"], party.website)
        self.assertEqual(context["descriptors"], party.descriptors)
        self.assertEqual(context["type"], get_value_from_enum(party.sub_type, SubType))
        if party.clearance_level:
            self.assertEqual(context["clearance_level"], PvGrading.to_str(party.clearance_level))

    def _assert_third_party(self, context, third_party):
        self.assertEqual(len(context["all"]), 1)
        self._assert_party(context["all"][0], third_party)
        self.assertEqual(len(context[third_party.role]), 1)
        self._assert_party(context[third_party.role][0], third_party)

    def _assert_good(self, context, good_on_application):
        good = context["good"]
        self.assertEqual(good["description"], good_on_application.good.description)
        self.assertEqual(
            good["control_list_entries"],
            [clc.rating for clc in good_on_application.good.control_list_entries.all()],
        )
        self.assertEqual(good["is_controlled"], GoodControlled.to_str(good_on_application.good.is_good_controlled))
        self.assertEqual(good["part_number"], good_on_application.good.part_number)
        self.assertTrue(str(good_on_application.quantity) in context["applied_for_quantity"])
        self.assertTrue(Units.to_str(good_on_application.unit) in context["applied_for_quantity"])
        self.assertEqual(context["applied_for_value"], f"£{good_on_application.value:.2f}")
        self.assertEqual(context["is_incorporated"], friendly_boolean(good_on_application.is_good_incorporated))
        if context.get("item_type"):
            self.assertEqual(context["item_type"], good_on_application.item_type)
            self.assertEqual(context["other_item_type"], good_on_application.other_item_type)

        # TAU
        self.assertEqual(good["item_category"], ItemCategory.to_str(good_on_application.good.item_category))

        if good_on_application.good.item_category in ItemCategory.group_one:
            self.assertEqual(good["is_military_use"], MilitaryUse.to_str(good_on_application.good.is_military_use))
            if good_on_application.good.is_military_use == MilitaryUse.YES_MODIFIED:
                self.assertEqual(
                    good["modified_military_use_details"], good_on_application.good.modified_military_use_details
                )
            self.assertEqual(good["is_component"], Component.to_str(good_on_application.good.is_component))
            if good_on_application.good.is_component != Component.NO:
                self.assertEqual(good["component_details"], good_on_application.good.component_details)
            self.assertEqual(
                good["uses_information_security"],
                friendly_boolean(good_on_application.good.uses_information_security),
            )
            if good_on_application.good.uses_information_security:
                self.assertEqual(
                    good["information_security_details"], good_on_application.good.information_security_details
                )
        elif context["firearm_details"] and good_on_application.good.item_category in ItemCategory.group_two:
            firearm_details = context["firearm_details"]
            self.assertEqual(firearm_details["type"], good_on_application.firearm_details.type)
            self.assertEqual(
                firearm_details["year_of_manufacture"], good_on_application.firearm_details.year_of_manufacture
            )

            self.assertEqual(firearm_details["calibre"], good_on_application.firearm_details.calibre)
            self.assertEqual(
                firearm_details["is_covered_by_firearm_act_section_one_two_or_five"],
                str(good_on_application.firearm_details.is_covered_by_firearm_act_section_one_two_or_five),
            )
            self.assertEqual(
                firearm_details["section_certificate_number"],
                good_on_application.firearm_details.section_certificate_number,
            )
            self.assertEqual(
                firearm_details["section_certificate_date_of_expiry"],
                good_on_application.firearm_details.section_certificate_date_of_expiry.strftime(DATE_FORMAT),
            )
            self.assertEqual(
                firearm_details["has_serial_numbers"],
                good_on_application.firearm_details.has_serial_numbers,
            )
            self.assertEqual(
                firearm_details["serial_numbers_available"],
                good_on_application.firearm_details.serial_numbers_available,
            )
        elif good_on_application.good.item_category in ItemCategory.group_three:
            self.assertEqual(good["is_military_use"], MilitaryUse.to_str(good_on_application.good.is_military_use))
            self.assertEqual(
                good["modified_military_use_details"], good_on_application.good.modified_military_use_details
            )
            self.assertEqual(
                good["software_or_technology_details"], good_on_application.good.software_or_technology_details
            )
            self.assertEqual(
                good["uses_information_security"],
                friendly_boolean(good_on_application.good.uses_information_security),
            )
            self.assertEqual(
                good["information_security_details"], good_on_application.good.information_security_details
            )

        # pv grading
        self.assertEqual(good["is_pv_graded"], GoodPvGraded.to_str(good_on_application.good.is_pv_graded))
        if good_on_application.good.pv_grading_details:
            if good_on_application.good.pv_grading_details.grading:
                self.assertEqual(
                    context["pv_grading"]["grading"],
                    PvGrading.to_str(good_on_application.good.pv_grading_details.grading),
                )
            else:
                self.assertEqual(
                    context["pv_grading"]["grading"], good_on_application.good.pv_grading_details.custom_grading
                )
            self.assertEqual(context["pv_grading"]["prefix"], good_on_application.good.pv_grading_details.prefix)
            self.assertEqual(context["pv_grading"]["suffix"], good_on_application.good.pv_grading_details.suffix)
            self.assertEqual(
                context["pv_grading"]["issuing_authority"],
                good_on_application.good.pv_grading_details.issuing_authority,
            )
            self.assertEqual(context["pv_grading"]["reference"], good_on_application.good.pv_grading_details.reference)
            self.assertEqual(
                context["pv_grading"]["date_of_issue"], good_on_application.good.pv_grading_details.date_of_issue
            )

    def _assert_good_on_licence(self, context, good_on_licence):
        self._assert_good(context, good_on_licence.good)
        self.assertTrue(Units.to_str(good_on_licence.good.unit) in context["quantity"])
        self.assertTrue(str(good_on_licence.quantity) in context["quantity"])
        self.assertTrue(str(good_on_licence.value) in context["value"])

    def _assert_good_with_advice(self, context, advice, good_on_application):
        goods = context[advice.type if advice.type != AdviceType.PROVISO else AdviceType.APPROVE]
        self.assertEqual(len(goods), 1)
        self._assert_good(goods[0], good_on_application)
        self.assertEqual(goods[0]["reason"], advice.text)
        self.assertEqual(goods[0]["note"], advice.note)
        self.assertEqual(goods[0]["proviso_reason"], advice.proviso)
        self.assertEqual(len(goods[0]["denial_reasons"]), advice.denial_reasons.count())

    def _assert_ecju_query(self, context, ecju_query):
        self.assertEqual(context["question"]["text"], ecju_query.question)
        self.assertEqual(
            context["question"]["user"],
            " ".join([ecju_query.raised_by_user.first_name, ecju_query.raised_by_user.last_name]),
        )
        self.assertIsNotNone(context["question"]["date"])
        self.assertIsNotNone(context["question"]["time"])
        self.assertEqual(context["response"]["text"], ecju_query.response)
        self.assertEqual(
            context["response"]["user"],
            " ".join([ecju_query.responded_by_user.first_name, ecju_query.responded_by_user.last_name]),
        )
        self.assertIsNotNone(context["response"]["date"])
        self.assertIsNotNone(context["response"]["time"])

    def _assert_note(self, context, note):
        self.assertEqual(context["text"], note.text)
        self.assertEqual(
            context["user"],
            " ".join([note.user.first_name, note.user.last_name]),
        )
        self.assertIsNotNone(context["date"])
        self.assertIsNotNone(context["time"])

    def _assert_site(self, context, site):
        self.assertEqual(context["name"], site.name)
        self._assert_address(context, site.address)

    def _assert_external_location(self, context, external_location):
        self.assertEqual(context["name"], external_location.name)
        self.assertEqual(context["address"], external_location.address)
        self.assertEqual(context["country"]["name"], external_location.country.name)
        self.assertEqual(context["country"]["code"], external_location.country.id)

    def _assert_document(self, context, document):
        self.assertEqual(context["id"], str(document.id))
        self.assertEqual(context["name"], document.name)
        self.assertEqual(context["description"], document.description)

    def _assert_temporary_export_details(self, context, case):
        self.assertEqual(context["temp_export_details"], case.temp_export_details)
        self.assertEqual(context["is_temp_direct_control"], case.is_temp_direct_control)
        self.assertEqual(context["temp_direct_control_details"], case.temp_direct_control_details)
        self.assertEqual(context["proposed_return_date"], case.proposed_return_date.strftime(DATE_FORMAT))

    def _assert_base_application_details(self, context, case):
        self.assertEqual(context["user_reference"], case.name)
        self.assertEqual(context["end_use_details"], case.intended_end_use)
        self.assertEqual(context["military_end_use_controls"], friendly_boolean(case.is_military_end_use_controls))
        self.assertEqual(context["military_end_use_controls_reference"], case.military_end_use_controls_ref)
        self.assertEqual(context["informed_wmd"], friendly_boolean(case.is_informed_wmd))
        self.assertEqual(context["informed_wmd_reference"], case.informed_wmd_ref)
        self.assertEqual(context["suspected_wmd"], friendly_boolean(case.is_suspected_wmd))
        self.assertEqual(context["suspected_wmd_reference"], case.suspected_wmd_ref)
        self.assertEqual(context["eu_military"], friendly_boolean(case.is_eu_military))
        self.assertEqual(context["compliant_limitations_eu"], friendly_boolean(case.is_compliant_limitations_eu))
        self.assertEqual(context["compliant_limitations_eu_reference"], case.compliant_limitations_eu_ref)

    def _assert_standard_application_details(self, context, case):
        self.assertEqual(context["export_type"], case.export_type)
        self.assertEqual(context["reference_number_on_information_form"], case.reference_number_on_information_form)
        self.assertEqual(context["has_been_informed"], case.have_you_been_informed)
        self.assertEqual(context["shipped_waybill_or_lading"], friendly_boolean(case.is_shipped_waybill_or_lading))
        self.assertEqual(context["non_waybill_or_lading_route_details"], case.non_waybill_or_lading_route_details)
        self.assertEqual(context["proposed_return_date"], case.proposed_return_date.strftime(DATE_FORMAT))
        self.assertEqual(context["trade_control_activity"], case.trade_control_activity)
        self.assertEqual(context["trade_control_activity_other"], case.trade_control_activity_other)
        self.assertEqual(context["trade_control_product_categories"], case.trade_control_product_categories)
        self._assert_temporary_export_details(context["temporary_export_details"], case)

    def _assert_destination_details(self, context, destination):
        self.assertEqual(context["country"]["name"], destination.country.name)
        self.assertEqual(context["country"]["code"], destination.country.id)
        self.assertEqual(context["contract_types"], destination.contract_types)
        self.assertEqual(context["other_contract_type"], destination.other_contract_type_text)

    def _assert_exhibition_clearance_details(self, context, case):
        self.assertEqual(context["exhibition_title"], case.title)
        self.assertEqual(context["first_exhibition_date"], case.first_exhibition_date.strftime(DATE_FORMAT))
        self.assertEqual(context["required_by_date"], case.required_by_date.strftime(DATE_FORMAT))
        self.assertEqual(context["reason_for_clearance"], case.reason_for_clearance)

    def _assert_end_user_advisory_details(self, context, case):
        self.assertEqual(context["note"], case.note)
        self.assertEqual(context["query_reason"], case.reasoning)
        self.assertEqual(context["nature_of_business"], case.nature_of_business)
        self.assertEqual(context["contact_name"], case.contact_name)
        self.assertEqual(context["contact_email"], case.contact_email)
        self.assertEqual(context["contact_job_title"], case.contact_job_title)
        self.assertEqual(context["contact_telephone"], case.contact_telephone)
        self._assert_party(context["end_user"], case.end_user)

    def _assert_goods_query_details(self, context, case):
        self.assertEqual(context["control_list_entry"], case.clc_control_list_entry)
        self.assertEqual(context["clc_raised_reasons"], case.clc_raised_reasons)
        self.assertEqual(context["pv_grading_raised_reasons"], case.pv_grading_raised_reasons)
        self.assertEqual(context["good"]["description"], case.good.description)
        self.assertEqual(
            context["good"]["control_list_entries"], [clc.rating for clc in case.good.control_list_entries.all()]
        )
        self.assertEqual(context["good"]["is_controlled"], case.good.is_good_controlled)
        self.assertEqual(context["good"]["part_number"], case.good.part_number)
        self.assertEqual(context["clc_responded"], friendly_boolean(case.clc_responded))
        self.assertEqual(context["pv_grading_responded"], friendly_boolean(case.pv_grading_responded))

    def _assert_case_type_details(self, context, case):
        self.assertEqual(context["type"], case.case_type.type)
        self.assertEqual(context["reference"], case.case_type.reference)
        self.assertEqual(context["sub_type"], case.case_type.sub_type)

    def test_generate_context_with_parties(self):
        # Standard application with all party types
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        self.create_party("Ultimate end user", self.organisation, PartyType.ULTIMATE_END_USER, case)

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self.assertIsNotNone(context["current_date"])
        self.assertIsNotNone(context["current_time"])
        self._assert_applicant(context["addressee"], case)
        self._assert_organisation(context["organisation"], self.organisation)
        self._assert_party(context["end_user"], case.end_user.party)
        self._assert_party(context["consignee"], case.consignee.party)
        self.assertEqual(len(context["ultimate_end_users"]), 1)
        self._assert_party(context["ultimate_end_users"][0], case.ultimate_end_users[0].party)
        # Third party should be in "all" list and role specific list
        self.assertEqual(len(context["third_parties"]), 2)
        self._assert_third_party(context["third_parties"], case.third_parties[0].party)

    def test_generate_context_with_custom_addressee(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        addressee = Party.objects.create(
            name="Joe Bloggs",
            address="123 test st.",
            organisation=self.organisation,
            type=PartyType.ADDITIONAL_CONTACT,
            phone_number="07123456789",
            country_id="GB",
        )

        context = get_document_context(case, addressee=addressee)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)
        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_addressee(context["addressee"], addressee)

    def test_generate_context_with_goods(self):
        application = self.create_standard_application_case(self.organisation, user=self.exporter_user, num_products=10)
        for product in application.goods.all():
            FinalAdviceFactory(user=self.gov_user, case=application, good=product.good)

        licence = StandardLicenceFactory(case=application, status=LicenceStatus.ISSUED)
        for product in application.goods.all():
            GoodOnLicenceFactory(
                good=product,
                licence=licence,
                quantity=product.quantity,
                usage=0.0,
                value=product.value,
            )

        context = get_document_context(application)
        # Ensure products order in generated template matches with the order in application
        order_in_application = [product.good.name for product in application.goods.all()]
        order_in_licence_template = [product["good"]["name"] for product in context["goods"]["approve"]]
        self.assertEqual(order_in_application, order_in_licence_template)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)
        self.assertEqual(context["case_reference"], application.reference_code)
        self.assertEqual(context["case_officer_name"], application.get_case_officer_name())

    def test_generate_context_with_goods_proviso_included(self):
        application = self.create_standard_application_case(self.organisation, user=self.exporter_user, num_products=10)

        # mixup approvals and proviso's to check the order later
        for index, product in enumerate(application.goods.all()):
            advice_type = AdviceType.PROVISO if index % 2 else AdviceType.APPROVE
            FinalAdviceFactory(user=self.gov_user, case=application, good=product.good, type=advice_type)

        licence = StandardLicenceFactory(case=application, status=LicenceStatus.ISSUED)
        for product in application.goods.all():
            GoodOnLicenceFactory(
                good=product,
                licence=licence,
                quantity=product.quantity,
                usage=0.0,
                value=product.value,
            )

        context = get_document_context(application)
        # Ensure products order in generated template matches with the order in application
        order_in_application = [product.good.name for product in application.goods.all()]
        order_in_licence_template = [product["good"]["name"] for product in context["goods"]["approve"]]
        self.assertEqual(order_in_application, order_in_licence_template)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)
        self.assertEqual(context["case_reference"], application.reference_code)
        self.assertEqual(context["case_officer_name"], application.get_case_officer_name())

    def test_generate_context_with_goods_proviso_included_and_multiple_goa_for_single_good(self):
        application = self.create_standard_application_case(self.organisation, user=self.exporter_user, num_products=10)
        single_good = application.goods.first().good

        # mixup approvals and proviso's to check the order later
        for index, product in enumerate(application.goods.all()):
            advice_type = AdviceType.PROVISO if index % 2 else AdviceType.APPROVE
            FinalAdviceFactory(user=self.gov_user, case=application, good=product.good, type=advice_type)

        licence = StandardLicenceFactory(case=application, status=LicenceStatus.ISSUED)
        for product in application.goods.all():
            GoodOnLicenceFactory(
                good=product,
                licence=licence,
                quantity=product.quantity,
                usage=0.0,
                value=product.value,
            )

        context = get_document_context(application)
        # Ensure products order in generated template matches with the order in application
        order_in_application = [product.good.name for product in application.goods.all()]
        order_in_licence_template = [product["good"]["name"] for product in context["goods"]["approve"]]
        self.assertEqual(len(order_in_application), len(order_in_licence_template))
        self.assertEqual(order_in_application, order_in_licence_template)

    def test_generate_context_with_advice_on_goods(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        good = case.goods.first()
        final_advice = FinalAdviceFactory(
            user=self.gov_user,
            case=case,
            type=AdviceType.REFUSE,
            good=good.good,
        )

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_good_with_advice(context["goods"], final_advice, case.goods.all()[0])

    def test_generate_context_with_advice_on_goods_missing(self):
        """This tests the scenario where advice had been given on a good, but then that
        good was subsequently removed from the application.
        """
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        another_good_on_application = GoodOnApplicationFactory(
            application=case,
            good=GoodFactory(organisation=self.organisation, is_good_controlled=True),
            quantity=10,
            unit=Units.NAR,
            value=500,
        )
        FinalAdviceFactory(
            user=self.gov_user,
            case=case,
            type=AdviceType.REFUSE,
            good=case.goods.first().good,
        )
        final_advice = FinalAdviceFactory(
            user=self.gov_user,
            case=case,
            type=AdviceType.REFUSE,
            good=another_good_on_application.good,
        )

        case.goods.first().delete()  # Remove the first good from the application

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_good_with_advice(context["goods"], final_advice, case.goods.all()[0])

    def test_generate_context_with_advice_on_goods_some_missing(self):
        """
        This tests the scenario where advice had been given on for two
        GoodOnApplications referring to the same Good.  After application editing,
        only one GoodOnApplication remains despite both advice records still being present.
        """
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        good = case.goods.first().good
        another_good_on_application = GoodOnApplicationFactory(
            application=case,
            good=good,
            quantity=10,
            unit=Units.NAR,
            value=500,
        )
        final_advice = FinalAdviceFactory(
            user=self.gov_user,
            case=case,
            type=AdviceType.REFUSE,
            good=good,
        )
        FinalAdviceFactory(
            user=self.gov_user,
            case=case,
            type=AdviceType.REFUSE,
            good=good,
        )

        case.goods.first().delete()  # Remove the first good from the application

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_good_with_advice(context["goods"], final_advice, case.goods.all()[0])

    def test_generate_context_with_proviso_advice_on_goods(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        good = case.goods.first()
        good.licenced_quantity = 15
        good.licenced_value = 20
        good.save()
        final_advice = FinalAdviceFactory(user=self.gov_user, case=case, type=AdviceType.PROVISO, good=good.good)

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_good_with_advice(context["goods"], final_advice, case.goods.all()[0])
        self.assertEqual(context["goods"][AdviceType.APPROVE][0]["proviso_reason"], final_advice.proviso)

    def test_goods_context_approve_has_quantity_and_value(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        good_on_application = case.goods.first()
        good = good_on_application.good
        FinalAdviceFactory(user=self.gov_user, case=case, good=good)

        licence = StandardLicenceFactory(case=case, status=LicenceStatus.ISSUED)
        GoodOnLicenceFactory(good=good_on_application, quantity=3, value=420, licence=licence)

        context = get_document_context(case)

        self.assertNotIn(AdviceType.PROVISO, context["goods"])
        self.assertEqual(context["goods"][AdviceType.APPROVE][0]["quantity"], "3.0 Items")
        self.assertEqual(context["goods"][AdviceType.APPROVE][0]["value"], "£420.00")

    def test_goods_context_proviso_has_quantity_and_value(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        good_on_application = case.goods.first()
        good = good_on_application.good
        FinalAdviceFactory(user=self.gov_user, case=case, good=good)
        FinalAdviceFactory(user=self.gov_user, case=case, good=good, type=AdviceType.PROVISO)

        licence = StandardLicenceFactory(case=case, status=LicenceStatus.ISSUED)
        good_on_licence = GoodOnLicenceFactory(good=good_on_application, quantity=3, value=420, licence=licence)

        context = get_document_context(case)

        self.assertEqual(context["goods"][AdviceType.APPROVE][0]["quantity"], "3.0 Items")
        self.assertEqual(context["goods"][AdviceType.APPROVE][0]["value"], "£420.00")

    @parameterized.expand([(date(2020, 1, 31),), (date(2020, 4, 30),), (date(2020, 10, 13),)])
    def test_generate_context_with_licence(self, start_date):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)

        licence = StandardLicenceFactory(case=case, status=LicenceStatus.ISSUED, start_date=start_date)
        good_on_licence = GoodOnLicenceFactory(
            good=case.goods.first(), quantity=10, usage=20, value=30, licence=licence
        )

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_licence(context["licence"], licence)
        self._assert_good_on_licence(context["goods"]["approve"][0], good_on_licence)

    def test_generate_context_with_ecju_query(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        ecju_query = self.create_ecju_query(case)
        ecju_query.response = "abc"
        ecju_query.responded_by_user = self.base_user
        ecju_query.save()

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_ecju_query(context["ecju_queries"][0], ecju_query)

    def test_generate_context_with_case_note(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        note = self.create_case_note(case, "text", self.gov_user.baseuser_ptr)

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_note(context["notes"][0], note)

    def test_generate_context_with_site(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        site = case.application_sites.first().site

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_site(context["sites"][0], site)

    def test_generate_context_with_external_locations(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        location = self.create_external_location("external", self.organisation)
        ExternalLocationOnApplication.objects.create(external_location=location, application=case)

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_external_location(context["external_locations"][0], location)

    def test_generate_context_with_document(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        document = self.create_application_document(case)

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)
        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_document(context["documents"][0], document)

    def test_generate_context_with_application_details(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)

        case.intended_end_use = "abc"
        case.is_military_end_use_controls = True
        case.military_end_use_controls_ref = "123"
        case.is_informed_wmd = False
        case.informed_wmd_ref = "456"
        case.is_suspected_wmd = True
        case.suspected_wmd_ref = "789"
        case.is_eu_military = False
        case.is_compliant_limitations_eu = None
        case.compliant_limitations_eu_ref = "012"
        case.save()

        case.baseapplication.refresh_from_db()

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)
        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_base_application_details(context["details"], case)

    def test_generate_context_with_standard_application_details(self):
        case = self.create_standard_application_case(self.organisation)
        case.export_type = ApplicationExportType.TEMPORARY
        case.reference_number_on_information_form = "123"
        case.has_you_been_informed = ApplicationExportLicenceOfficialType.YES
        case.shipped_waybill_or_lading = False
        case.non_waybill_or_lading_route_details = "abc"
        case.proposed_return_date = date(year=2020, month=1, day=1)
        case.trade_control_activity = TradeControlActivity.MARITIME_ANTI_PIRACY
        case.trade_control_activity_other = "other"
        case.trade_control_product_categories = [TradeControlProductCategory.CATEGORY_A]
        case.save()

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_submitted_at"], case.submitted_at)
        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_case_type_details(context["case_type"], case)
        self._assert_base_application_details(context["details"], case)
        self._assert_standard_application_details(context["details"], case)

    @freeze_time("2025-04-22")
    def test_generate_context_with_f680_details(self):
        f680_application = SubmittedF680ApplicationFactory(application={"some": "json"})

        queue = Queue.objects.get(id=QueuesEnum.MOD_ECJU_F680_CASES_UNDER_FINAL_REVIEW)
        CaseAssignmentFactory(case=f680_application, user=self.gov_user, queue=queue)

        approved_release = F680SecurityReleaseRequestFactory(application=f680_application)
        refused_release = F680SecurityReleaseRequestFactory(application=f680_application)
        all_activities = dict(ApprovalTypes.choices)
        approved_activities = [
            ApprovalTypes.INITIAL_DISCUSSION_OR_PROMOTING,
            ApprovalTypes.DEMONSTRATION_OVERSEAS,
            ApprovalTypes.TRAINING,
        ]

        approval_outcome = F680SecurityReleaseOutcomeFactory(
            case=f680_application, outcome="approve", approval_types=approved_activities
        )
        approval_outcome.security_release_requests.set([approved_release])

        refusal_outcome = F680SecurityReleaseOutcomeFactory(case=f680_application, outcome="refuse")
        refusal_outcome.security_release_requests.set([refused_release])

        approval_security_release_data = SecurityReleaseRequestSerializer(
            approval_outcome.security_release_requests.all(), many=True
        ).data
        refusal_security_release_data = SecurityReleaseRequestSerializer(
            refusal_outcome.security_release_requests.all(), many=True
        ).data

        context = get_document_context(f680_application)

        expected_approval_activities = [
            {
                "key": item,
                "value": all_activities[item],
                "status": "Approved" if item in approved_activities else "Refused",
            }
            for item in approved_release.approval_types
        ]
        expected_refusal_activities = [
            {
                "key": item,
                "value": all_activities[item],
                "status": "Refused",
            }
            for item in refused_release.approval_types
        ]
        validity_start_date = timezone.now().date().isoformat()
        validity_end_date = (timezone.now().date() + relativedelta(months=24)).strftime("%d %B %Y")

        assert context["details"]["application"] == {"some": "json"}
        assert context["details"]["case_officer"] == self.gov_user

        assert context["details"]["security_release_outcomes"] == {
            "approve": [
                {
                    "security_release_requests": approval_security_release_data,
                    "outcome": approval_outcome.outcome,
                    "conditions": approval_outcome.conditions,
                    "refusal_reasons": approval_outcome.refusal_reasons,
                    "security_grading": approval_outcome.security_grading,
                    "approval_types": expected_approval_activities,
                    "validity_start_date": validity_start_date,
                    "validity_end_date": validity_end_date,
                    "validity_period": 24,
                }
            ],
            "refuse": [
                {
                    "security_release_requests": refusal_security_release_data,
                    "outcome": refusal_outcome.outcome,
                    "conditions": refusal_outcome.conditions,
                    "refusal_reasons": refusal_outcome.refusal_reasons,
                    "security_grading": refusal_outcome.security_grading,
                    "approval_types": expected_refusal_activities,
                    "validity_start_date": validity_start_date,
                    "validity_end_date": validity_end_date,
                    "validity_period": 0,
                }
            ],
        }

    def test_generate_context_with_end_user_advisory_query_details(self):
        case = self.create_end_user_advisory(note="abc", reasoning="def", organisation=self.organisation)

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_end_user_advisory_details(context["details"], case)

    def test_generate_context_with_goods_query_details(self):
        case = self.create_goods_query("abc", self.organisation, "clc reason", "pv reason")

        context = get_document_context(case)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], case.reference_code)
        self.assertEqual(context["case_officer_name"], case.get_case_officer_name())
        self._assert_goods_query_details(context["details"], case)

    def test_generate_context_with_category_1_good_details(self):
        application = self.create_standard_application_case(self.organisation)
        application.goods.all().delete()
        good = GoodFactory(
            organisation=self.organisation,
            is_military_use=MilitaryUse.YES_MODIFIED,
            is_component=Component.YES_MODIFIED,
            component_details="many details",
            uses_information_security=True,
            information_security_details="information security details",
            modified_military_use_details="modified reasons",
        )
        application.goods.all().delete()
        goa = GoodOnApplicationFactory(
            application=application, good=good, quantity=100.0, value=1500.00, unit=Units.NAR
        )

        context = get_document_context(application)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], application.reference_code)
        self._assert_good(context["goods"]["all"][0], goa)

    def test_generate_context_with_category_3_good_details(self):
        application = self.create_standard_application_case(self.organisation)
        application.goods.all().delete()
        good = GoodFactory(
            organisation=self.organisation,
            item_category=ItemCategory.GROUP3_SOFTWARE,
            is_military_use=MilitaryUse.YES_MODIFIED,
            modified_military_use_details="modified reasons",
            software_or_technology_details="software and technology details",
            uses_information_security=True,
            information_security_details="information security details",
        )
        application.goods.all().delete()
        goa = GoodOnApplicationFactory(
            application=application, good=good, quantity=100.0, value=1500.00, unit=Units.NAR
        )

        context = get_document_context(application)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], application.reference_code)
        self._assert_good(context["goods"]["all"][0], goa)

    def test_generate_context_with_category_2_good_details_legacy(self):
        application = self.create_standard_application_case(self.organisation)
        application.goods.all().delete()
        firearm_details = FirearmFactory()
        good = GoodFactory(
            organisation=self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, firearm_details=firearm_details
        )
        application.goods.all().delete()
        goa: GoodOnApplication = GoodOnApplicationFactory(
            application=application, good=good, quantity=100.0, value=1500.00, unit=Units.NAR
        )

        context = get_document_context(application)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        # in the case of a legacy case context should fall back to the firearms
        # details on a good.
        goa.firearm_details = goa.good.firearm_details

        self.assertEqual(context["case_reference"], application.reference_code)
        self._assert_good(context["goods"]["all"][0], goa)

    def test_generate_context_with_category_2_good_details(self):
        application = self.create_standard_application_case(self.organisation)
        application.goods.all().delete()
        firearm_details = FirearmFactory(year_of_manufacture=2020)
        firearm_details_on_application = FirearmFactory(year_of_manufacture=1919)
        good = GoodFactory(
            organisation=self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, firearm_details=firearm_details
        )
        application.goods.all().delete()
        goa: GoodOnApplication = GoodOnApplicationFactory(
            application=application,
            good=good,
            quantity=100.0,
            value=1500.00,
            unit=Units.NAR,
            firearm_details=firearm_details_on_application,
        )

        context = get_document_context(application)
        render_to_string(template_name="letter_templates/case_context_test.html", context=context)

        self.assertEqual(context["case_reference"], application.reference_code)
        self._assert_good(context["goods"]["all"][0], goa)


class SerializersTests(DataTestClient):
    def test_EcjuQuerySerializer_format(self):
        ecju_query = EcjuQueryFactory()
        serialized = EcjuQuerySerializer(ecju_query)

        assert set(serialized.data.keys()) == {"question", "response"}
        assert serialized.data["question"]["text"] == "why x in y?"
        assert serialized.data["question"]["user"]
        assert serialized.data["question"]["created_at"]
        assert (
            str(serialized.data["question"]["raised_by_user"]).count("-") == 4
        )  # e.g. '81586396-1b1d-4e06-92f6-592669c62f45'
        assert serialized.data["question"]["question"] == "why x in y?"
        assert serialized.data["question"]["date"]
        assert serialized.data["question"]["time"]
        assert serialized.data["response"]["text"] == "because of z"
        assert serialized.data["response"]["user"] == "N/A"
        assert serialized.data["response"]["created_at"]
        assert serialized.data["response"]["responded_by_user"] == None
        assert serialized.data["response"]["response"] == "because of z"
        assert serialized.data["response"]["date"]
        assert serialized.data["response"]["time"]
