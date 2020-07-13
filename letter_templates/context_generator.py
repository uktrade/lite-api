from django.contrib.humanize.templatetags.humanize import intcomma

from applications.enums import GoodsTypeCategory, MTCRAnswers, ServiceEquipmentType
from applications.models import (
    ApplicationDocument,
    StandardApplication,
    OpenApplication,
    ExhibitionClearanceApplication,
    F680ClearanceApplication,
    HmrcQuery,
    CountryOnApplication,
)
from cases.enums import AdviceLevel, AdviceType, CaseTypeSubTypeEnum
from cases.models import Advice, EcjuQuery, CaseNote, GoodCountryDecision
from compliance.models import ComplianceVisitCase, CompliancePerson
from conf.helpers import get_date_and_time, add_months, DATE_FORMAT, TIME_FORMAT, friendly_boolean, pluralise_unit
from goods.enums import PvGrading
from licences.models import Licence
from organisations.models import Site, ExternalLocation
from parties.enums import PartyRole
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queries.goods_query.models import GoodsQuery
from static.f680_clearance_types.enums import F680ClearanceTypeEnum
from static.units.enums import Units


def get_document_context(case, addressee=None):
    """
    Generate universal context dictionary to provide data for all document types.
    """
    date, time = get_date_and_time()
    licence = Licence.objects.get_draft_or_active_licence(case.pk)
    final_advice = Advice.objects.filter(level=AdviceLevel.FINAL, case_id=case.pk)
    ecju_queries = EcjuQuery.objects.filter(case=case)
    notes = CaseNote.objects.filter(case=case)
    sites = Site.objects.filter(sites_on_application__application_id=case.pk)
    external_locations = ExternalLocation.objects.filter(external_locations_on_application__application_id=case.pk)
    documents = ApplicationDocument.objects.filter(application_id=case.pk).order_by("-created_at")
    destinations = CountryOnApplication.objects.filter(application_id=case.pk).order_by("country__name")
    base_application = case.baseapplication if getattr(case, "baseapplication", "") else None

    if getattr(base_application, "goods", "") and base_application.goods.exists():
        goods = _get_goods_context(base_application, final_advice, licence)
    elif getattr(base_application, "goods_type", "") and base_application.goods_type.exists():
        goods = _get_goods_type_context(base_application.goods_type.all(), case.pk)
    else:
        goods = None

    # compliance type cases contain neither an addressee or submitted_by user
    if not addressee and case.submitted_by:
        addressee = case.submitted_by

    return {
        "case_reference": case.reference_code,
        "case_type": {
            "type": case.case_type.type,
            "sub_type": case.case_type.sub_type,
            "reference": case.case_type.reference,
        },
        "current_date": date,
        "current_time": time,
        "details": _get_details_context(case),
        "addressee": _get_addressee_context(addressee) if addressee else None,
        "organisation": _get_organisation_context(case.organisation),
        "licence": _get_licence_context(licence) if licence else None,
        "end_user": _get_party_context(base_application.end_user.party)
        if base_application and getattr(base_application, "end_user", "")
        else None,
        "consignee": _get_party_context(base_application.consignee.party)
        if base_application and getattr(base_application, "consignee", "")
        else None,
        "ultimate_end_users": [
            _get_party_context(ultimate_end_user.party) for ultimate_end_user in base_application.ultimate_end_users
        ]
        if getattr(base_application, "ultimate_end_users", "")
        else [],
        "third_parties": _get_third_parties_context(base_application.third_parties)
        if getattr(base_application, "third_parties", "")
        else [],
        "goods": goods,
        "ecju_queries": [_get_ecju_query_context(query) for query in ecju_queries],
        "notes": [_get_case_note_context(note) for note in notes],
        "sites": [_get_site_context(site) for site in sites],
        "external_locations": [_get_external_location_context(location) for location in external_locations],
        "documents": [_get_document_context(document) for document in documents],
        "destinations": [_get_destination_context(destination) for destination in destinations],
    }


def _get_address(address):
    return {
        "address_line_1": address.address_line_1 or address.address,
        "address_line_2": address.address_line_2,
        "postcode": address.postcode,
        "city": address.city,
        "region": address.region,
        "country": {"name": address.country.name, "code": address.country.id,},
    }


def _get_base_application_details_context(application):
    return {
        "user_reference": application.name,
        "end_use_details": getattr(application, "intended_end_use", ""),
        "military_end_use_controls": friendly_boolean(getattr(application, "is_military_end_use_controls", "")),
        "military_end_use_controls_reference": getattr(application, "military_end_use_controls_ref", ""),
        "informed_wmd": friendly_boolean(getattr(application, "is_informed_wmd", "")),
        "informed_wmd_reference": getattr(application, "informed_wmd_ref", ""),
        "suspected_wmd": friendly_boolean(getattr(application, "is_suspected_wmd", "")),
        "suspected_wmd_reference": getattr(application, "suspected_wmd_ref", ""),
        "eu_military": friendly_boolean(getattr(application, "is_eu_military", "")),
        "compliant_limitations_eu": friendly_boolean(getattr(application, "is_compliant_limitations_eu", "")),
        "compliant_limitations_eu_reference": getattr(application, "compliant_limitations_eu_ref", ""),
    }


def _get_standard_application_context(case):
    context = _get_base_application_details_context(case.baseapplication)
    standard_application = StandardApplication.objects.get(id=case.pk)
    context.update(
        {
            "export_type": standard_application.export_type,
            "reference_number_on_information_form": standard_application.reference_number_on_information_form,
            "has_been_informed": standard_application.have_you_been_informed,
            "shipped_waybill_or_lading": friendly_boolean(standard_application.is_shipped_waybill_or_lading),
            "non_waybill_or_lading_route_details": standard_application.non_waybill_or_lading_route_details,
            "proposed_return_date": standard_application.proposed_return_date.strftime(DATE_FORMAT)
            if standard_application.proposed_return_date
            else None,
            "trade_control_activity": standard_application.trade_control_activity,
            "trade_control_activity_other": standard_application.trade_control_activity_other,
            "trade_control_product_categories": standard_application.trade_control_product_categories,
            "temporary_export_details": _get_temporary_export_details(standard_application),
        }
    )
    return context


def _get_open_application_context(case):
    context = _get_base_application_details_context(case.baseapplication)
    open_application = OpenApplication.objects.get(id=case.pk)
    context.update(
        {
            "export_type": open_application.export_type,
            "contains_firearm_goods": friendly_boolean(open_application.contains_firearm_goods),
            "shipped_waybill_or_lading": friendly_boolean(open_application.is_shipped_waybill_or_lading),
            "non_waybill_or_lading_route_details": open_application.non_waybill_or_lading_route_details,
            "proposed_return_date": open_application.proposed_return_date.strftime(DATE_FORMAT)
            if open_application.proposed_return_date
            else None,
            "trade_control_activity": open_application.trade_control_activity,
            "trade_control_activity_other": open_application.trade_control_activity_other,
            "trade_control_product_categories": open_application.trade_control_product_categories,
            "goodstype_category": GoodsTypeCategory.get_text(open_application.goodstype_category)
            if open_application.goodstype_category
            else None,
            "temporary_export_details": _get_temporary_export_details(open_application),
        }
    )
    return context


def _get_hmrc_query_context(case):
    context = _get_base_application_details_context(case.baseapplication)
    hmrc_query = HmrcQuery.objects.get(id=case.pk)
    context.update(
        {"query_reason": hmrc_query.reasoning, "have_goods_departed": friendly_boolean(hmrc_query.have_goods_departed),}
    )
    return context


def _get_exhibition_clearance_context(case):
    context = _get_base_application_details_context(case.baseapplication)
    exhibition = ExhibitionClearanceApplication.objects.get(id=case.pk)
    context.update(
        {
            "exhibition_title": exhibition.title,
            "first_exhibition_date": exhibition.first_exhibition_date.strftime(DATE_FORMAT)
            if exhibition.first_exhibition_date
            else None,
            "required_by_date": exhibition.required_by_date.strftime(DATE_FORMAT)
            if exhibition.required_by_date
            else None,
            "reason_for_clearance": exhibition.reason_for_clearance,
        }
    )
    return context


def _get_f680_clearance_context(case):
    context = _get_base_application_details_context(case.baseapplication)
    f680 = F680ClearanceApplication.objects.get(id=case.pk)
    context.update(
        {
            "clearance_types": [F680ClearanceTypeEnum.get_text(f680_type.name) for f680_type in f680.types.all()],
            "expedited": friendly_boolean(f680.expedited),
            "expedited_date": f680.expedited_date.strftime(DATE_FORMAT) if f680.expedited_date else None,
            "foreign_technology": friendly_boolean(f680.foreign_technology),
            "foreign_technology_description": f680.foreign_technology_description,
            "locally_manufactured": friendly_boolean(f680.locally_manufactured),
            "locally_manufactured_description": f680.locally_manufactured_description,
            "mtcr_type": MTCRAnswers.choices_as_dict.get(f680.mtcr_type) if f680.mtcr_type else None,
            "electronic_warfare_requirement": friendly_boolean(f680.electronic_warfare_requirement),
            "uk_service_equipment": friendly_boolean(f680.uk_service_equipment),
            "uk_service_equipment_description": f680.uk_service_equipment_description,
            "uk_service_equipment_type": ServiceEquipmentType.choices_as_dict.get(f680.uk_service_equipment_type)
            if f680.uk_service_equipment_type
            else None,
            "prospect_value": f680.prospect_value,
            "clearance_level": PvGrading.choices_as_dict.get(f680.clearance_level),
        }
    )
    return context


def _get_gifting_clearance_context(case):
    context = _get_base_application_details_context(case.baseapplication)

    return context


def _get_end_user_advisory_query_context(case):
    query = EndUserAdvisoryQuery.objects.get(id=case.pk)
    return {
        "note": query.note,
        "query_reason": query.reasoning,
        "nature_of_business": query.nature_of_business,
        "contact_name": query.contact_name,
        "contact_email": query.contact_email,
        "contact_job_title": query.contact_job_title,
        "contact_telephone": query.contact_telephone,
        "end_user": _get_party_context(query.end_user),
    }


def _get_goods_query_context(case):
    def _get_goods_query_good_context(good):
        return {
            "description": good.description,
            "control_list_entries": [clc.rating for clc in good.control_list_entries.all()],
            "is_controlled": good.is_good_controlled,
            "part_number": good.part_number,
        }

    query = GoodsQuery.objects.get(id=case.pk)
    return {
        "control_list_entry": query.clc_control_list_entry,
        "clc_raised_reasons": query.clc_raised_reasons,
        "pv_grading_raised_reasons": query.pv_grading_raised_reasons,
        "good": _get_goods_query_good_context(query.good) if query.good else None,
        "clc_responded": friendly_boolean(query.clc_responded),
        "pv_grading_responded": friendly_boolean(query.pv_grading_responded),
    }


def _get_compliance_site_context(case):
    return None


def _get_compliance_visit_context(case):
    def _get_people_present_compliance_visit_context(case):
        people = list(CompliancePerson.objects.filter(visit_case=case.id))
        if people:
            return [{"name": person.name, "job_title": person.job_title} for person in people]
        else:
            return None

    comp_case = ComplianceVisitCase.objects.select_related("site_case").get(id=case.id)
    return {
        "site_case_reference": comp_case.site_case.reference_code,
        "site_name": comp_case.site_case.site.name,
        "site_address": comp_case.site_case.site.address,
        "visit_type": comp_case.visit_type,
        "visit_date": comp_case.visit_date,
        "overall_risk_value": comp_case.overall_risk_value,
        "licence_risk_value": comp_case.licence_risk_value,
        "overview": comp_case.overview,
        "inspection": comp_case.inspection,
        "compliance_overview": comp_case.compliance_overview,
        "compliance_risk_value": comp_case.compliance_risk_value,
        "individuals_overview": comp_case.individuals_overview,
        "individuals_risk_value": comp_case.individuals_risk_value,
        "products_overview": comp_case.products_overview,
        "products_risk_value": comp_case.products_risk_value,
        "people_present": _get_people_present_compliance_visit_context(comp_case),
    }


def _get_details_context(case):
    case_sub_type = case.case_type.sub_type
    if case_sub_type == CaseTypeSubTypeEnum.STANDARD:
        return _get_standard_application_context(case)
    elif case_sub_type == CaseTypeSubTypeEnum.OPEN:
        return _get_open_application_context(case)
    elif case_sub_type == CaseTypeSubTypeEnum.HMRC:
        return _get_hmrc_query_context(case)
    elif case_sub_type == CaseTypeSubTypeEnum.EXHIBITION:
        return _get_exhibition_clearance_context(case)
    elif case_sub_type == CaseTypeSubTypeEnum.F680:
        return _get_f680_clearance_context(case)
    elif case_sub_type == CaseTypeSubTypeEnum.GIFTING:
        return _get_gifting_clearance_context(case)
    elif case_sub_type == CaseTypeSubTypeEnum.EUA:
        return _get_end_user_advisory_query_context(case)
    elif case_sub_type == CaseTypeSubTypeEnum.GOODS:
        return _get_goods_query_context(case)
    elif case_sub_type == CaseTypeSubTypeEnum.COMP_SITE:
        return _get_compliance_site_context(case)
    elif case_sub_type == CaseTypeSubTypeEnum.COMP_VISIT:
        return _get_compliance_visit_context(case)
    else:
        return None


def _get_addressee_context(addressee):
    return {
        "name": " ".join([addressee.first_name, addressee.last_name])
        if hasattr(addressee, "first_name")
        else addressee.name,
        "email": addressee.email,
        "address": getattr(addressee, "address", ""),
        "phone_number": getattr(addressee, "phone_number", ""),
    }


def _get_organisation_context(organisation):
    return {
        "name": organisation.name,
        "eori_number": organisation.eori_number,
        "sic_number": organisation.sic_number,
        "vat_number": organisation.vat_number,
        "registration_number": organisation.registration_number,
        "primary_site": {"name": organisation.primary_site.name, **_get_address(organisation.primary_site.address)},
    }


def _get_licence_context(licence):
    return {
        "start_date": licence.start_date.strftime(DATE_FORMAT),
        "duration": licence.duration,
        "end_date": add_months(licence.start_date, licence.duration),
    }


def _get_party_context(party):
    return {
        "name": party.name,
        "type": party.sub_type,
        "address": party.address,
        "descriptors": party.descriptors,
        "country": {"name": party.country.name, "code": party.country.id},
        "website": party.website,
        "clearance_level": PvGrading.choices_as_dict.get(party.clearance_level),
    }


def _get_third_parties_context(third_parties):
    third_parties_context = {"all": [_get_party_context(third_party.party) for third_party in third_parties]}

    # Split third parties into lists based on role
    for role, _ in PartyRole.choices:
        third_parties_of_type = third_parties.filter(party__role=role)
        if third_parties_of_type:
            third_parties_context[role] = [
                _get_party_context(third_party.party) for third_party in third_parties_of_type
            ]

    return third_parties_context


def _format_quantity(quantity, unit):
    if quantity and unit:
        return " ".join([intcomma(quantity), pluralise_unit(Units.choices_as_dict[unit], quantity),])
    elif unit:
        return "0 " + pluralise_unit(Units.choices_as_dict[unit], quantity)


def _get_good_on_application_context(good_on_application, advice=None):
    good_context = {
        "description": good_on_application.good.description,
        "control_list_entries": [clc.rating for clc in good_on_application.good.control_list_entries.all()],
        "is_controlled": good_on_application.good.is_good_controlled,
        "part_number": good_on_application.good.part_number,
        "applied_for_quantity": _format_quantity(good_on_application.quantity, good_on_application.unit)
        if good_on_application.quantity
        else None,
        "applied_for_value": f"£{good_on_application.value}",
        "is_incorporated": friendly_boolean(good_on_application.is_good_incorporated),
    }
    if advice:
        good_context["reason"] = advice.text
        good_context["note"] = advice.note
        if advice.proviso:
            good_context["proviso_reason"] = advice.proviso
    if good_on_application.item_type:
        good_context["item_type"] = good_on_application.item_type
        good_context["other_item_type"] = good_on_application.other_item_type

    return good_context


def _get_good_on_licence_context(good_on_licence, advice=None):
    good_context = _get_good_on_application_context(good_on_licence.good, advice)
    good_context["quantity"] = _format_quantity(good_on_licence.quantity, good_on_licence.good.unit)
    good_context["value"] = f"£{good_on_licence.value}"

    return good_context


def _get_goods_context(application, final_advice, licence=None):
    goods_on_application = application.goods.all().order_by("good__description")
    final_advice = final_advice.filter(good_id__isnull=False)
    goods_context = {advice_type: [] for advice_type, _ in AdviceType.choices}

    goods_on_application_dict = {
        good_on_application.good_id: good_on_application for good_on_application in goods_on_application
    }
    goods_context["all"] = [_get_good_on_application_context(good) for good in goods_on_application]

    if licence:
        goods_on_licence = licence.goods.all().order_by("good__good__description")
        if goods_on_licence.exists():
            goods_context[AdviceType.APPROVE] = [
                _get_good_on_licence_context(good_on_licence) for good_on_licence in goods_on_licence
            ]
        # Remove APPROVE from advice as it is no longer needed
        # (no need to get approved GoodOnApplications if we have GoodOnLicence)
        final_advice = final_advice.exclude(type=AdviceType.APPROVE)

    for advice in final_advice:
        good_on_application = goods_on_application_dict[advice.good_id]
        goods_context[advice.type].append(_get_good_on_application_context(good_on_application, advice))

    # Move proviso elements into approved because they are treated the same
    goods_context[AdviceType.APPROVE].extend(goods_context.pop(AdviceType.PROVISO))
    return goods_context


def _get_goods_type(goods_type):
    return {
        "description": goods_type.description,
        "control_list_entries": [clc.rating for clc in goods_type.control_list_entries.all()],
        "is_controlled": friendly_boolean(goods_type.is_good_controlled),
    }


def _get_goods_type_decision_context(good_country_decisions):
    context = {}
    for decision in good_country_decisions:
        if decision.country.name not in context:
            context[decision.country.name] = [_get_goods_type(decision.goods_type)]
        else:
            context[decision.country.name].append(_get_goods_type(decision.goods_type))
    return context


def _get_goods_type_context(goods_types, case_pk):
    goods_type_context = {"all": [_get_goods_type(goods_type) for goods_type in goods_types]}

    approved_goods_type_on_country_decisions = GoodCountryDecision.objects.filter(
        case_id=case_pk, approve=True
    ).prefetch_related("goods_type", "country")
    if approved_goods_type_on_country_decisions:
        goods_type_context[AdviceType.APPROVE] = _get_goods_type_decision_context(
            approved_goods_type_on_country_decisions
        )

    refused_goods_type_on_country_decisions = GoodCountryDecision.objects.filter(
        case_id=case_pk, approve=False
    ).prefetch_related("goods_type", "country")
    if refused_goods_type_on_country_decisions:
        goods_type_context[AdviceType.REFUSE] = _get_goods_type_decision_context(
            refused_goods_type_on_country_decisions
        )

    return goods_type_context


def _get_ecju_query_context(query):
    query_context = {
        "question": {
            "text": query.question,
            "user": " ".join([query.raised_by_user.first_name, query.raised_by_user.last_name]),
            "date": query.created_at.strftime(DATE_FORMAT),
            "time": query.created_at.strftime(TIME_FORMAT),
        }
    }

    if query.response:
        query_context["response"] = {
            "text": query.response,
            "user": " ".join([query.responded_by_user.first_name, query.responded_by_user.last_name]),
            "date": query.responded_at.strftime(DATE_FORMAT),
            "time": query.responded_at.strftime(TIME_FORMAT),
        }

    return query_context


def _get_case_note_context(note):
    return {
        "text": note.text,
        "user": " ".join([note.user.first_name, note.user.last_name]),
        "date": note.created_at.strftime(DATE_FORMAT),
        "time": note.created_at.strftime(TIME_FORMAT),
        "visible_to_exporter": note.is_visible_to_exporter,
    }


def _get_site_context(site):
    return {"name": site.name, **_get_address(site.address)}


def _get_external_location_context(location):
    return {
        "name": location.name,
        "address": location.address,
        "country": {"name": location.country.name, "code": location.country.id},
    }


def _get_document_context(document):
    return {"id": str(document.id), "name": document.name, "description": document.description}


def _get_temporary_export_details(application):
    return {
        "temp_export_details": application.temp_export_details,
        "is_temp_direct_control": friendly_boolean(application.is_temp_direct_control),
        "temp_direct_control_details": application.temp_direct_control_details,
        "proposed_return_date": application.proposed_return_date,
    }


def _get_destination_context(destination):
    return {
        "country": {"code": destination.country.id, "name": destination.country.name,},
        "contract_types": destination.contract_types,
        "other_contract_type": destination.other_contract_type_text,
    }
