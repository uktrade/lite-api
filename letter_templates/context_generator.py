from audit_trail.models import Audit
from cases.enums import AdviceLevel, AdviceType
from cases.models import Advice, EcjuQuery, CaseNote
from conf.helpers import get_date_and_time, add_months, DATE_FORMAT, TIME_FORMAT
from licences.models import Licence
from organisations.models import Site
from parties.enums import PartyRole


def _get_address(address):
    return {
        "address_line_1": address.address_line_1 or address.address,
        "address_line_2": address.address_line_2,
        "postcode": address.postcode,
        "city": address.city,
        "region": address.region,
        "country": {
            "name": address.country.name,
            "code": address.country.id,
        }
    }


def _get_details_context(case):
    return {
        "end_use_details": case.baseapplication.intended_end_use if hasattr(case, "baseapplication") else None,
    }


def _get_applicant_context(applicant):
    return {"name": " ".join([applicant.first_name, applicant.last_name]), "email": applicant.email}


def _get_organisation_context(organisation):
    return {
        "name": organisation.name,
        "eori_number": organisation.eori_number,
        "sic_number": organisation.sic_number,
        "vat_number": organisation.vat_number,
        "registration_number": organisation.registration_number,
        "primary_site": {
            "name": organisation.primary_site.name,
            **_get_address(organisation.primary_site.address)
        },
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
        "address": party.address,
        "country": {"name": party.country.name, "code": party.country.id,},
        "website": party.website,
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


def _get_good_context(good_on_application, advice=None):
    good_context = {
        "description": good_on_application.good.description,
        "control_list_entries": [clc.rating for clc in good_on_application.good.control_list_entries.all()],
        "is_controlled": good_on_application.good.is_good_controlled,
        "part_number": good_on_application.good.part_number,
    }
    if advice:
        good_context["reason"] = advice.text
        good_context["note"] = advice.note
        if advice.proviso:
            good_context["proviso_reason"] = advice.proviso
    if good_on_application.licenced_quantity:
        good_context["quantity"] = good_on_application.licenced_quantity
    if good_on_application.licenced_value:
        good_context["value"] = good_on_application.licenced_value
    return good_context


def _get_goods_context(goods, final_advice):
    final_advice = final_advice.filter(good_id__isnull=False)
    goods = goods.all().order_by("good__description")
    goods_context = {advice_type: [] for advice_type, _ in AdviceType.choices}
    goods_context["all"] = [_get_good_context(good_on_application) for good_on_application in goods]
    goods_on_application = {good_on_application.good_id: good_on_application for good_on_application in goods}

    for advice in final_advice:
        good_on_application = goods_on_application[advice.good_id]
        goods_context[advice.type].append(_get_good_context(good_on_application, advice))

    # Move proviso elements into approved because they are treated the same
    goods_context[AdviceType.APPROVE].extend(goods_context.pop(AdviceType.PROVISO))
    return goods_context


def _get_goods_type_context(goods_type):
    goods_type_context = {}
    countries = set(goods_type.values_list("countries", "countries__name"))

    for country_id, country_name in countries:
        goods = goods_type.filter(countries=country_id)
        goods_type_context[country_name] = [
            {
                "description": good.description,
                "control_list_entries": [clc.rating for clc in good.control_list_entries.all()],
            }
            for good in goods
        ]

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
    }


def _get_site_context(site):
    return {
        "name": site.name,
        **_get_address(site.address)
    }


def get_document_context(case):
    date, time = get_date_and_time()
    licence = Licence.objects.filter(application_id=case.pk).order_by("-created_at").first()
    applicant_audit = Audit.objects.filter(target_object_id=case.id).first()
    final_advice = Advice.objects.filter(level=AdviceLevel.FINAL, case_id=case.pk)
    ecju_queries = EcjuQuery.objects.filter(case=case)
    notes = CaseNote.objects.filter(case=case)
    sites = Site.objects.filter(sites_on_application__application_id=case.pk)

    return {
        "reference": case.reference_code,
        "date": date,
        "time": time,
        "details": _get_details_context(case),
        "applicant": _get_applicant_context(applicant_audit.actor) if applicant_audit else None,
        "organisation": _get_organisation_context(case.organisation),
        "licence": _get_licence_context(licence) if licence else None,
        "end_user": _get_party_context(case.end_user.party) if hasattr(case, "end_user") and case.end_user else None,
        "consignee": _get_party_context(case.consignee.party)
        if hasattr(case, "consignee") and case.consignee
        else None,
        "ultimate_end_users": [
            _get_party_context(ultimate_end_user.party) for ultimate_end_user in case.ultimate_end_users
        ]
        if hasattr(case, "ultimate_end_users") and case.ultimate_end_users
        else [],
        "third_parties": _get_third_parties_context(case.third_parties)
        if hasattr(case, "third_parties") and case.third_parties
        else [],
        "goods": _get_goods_context(case.goods, final_advice) if hasattr(case, "goods") and case.goods else None,
        "goods_type": _get_goods_type_context(case.goods_type)
        if hasattr(case, "goods_type") and case.goods_type
        else None,
        "ecju_queries": [_get_ecju_query_context(query) for query in ecju_queries],
        "notes": [_get_case_note_context(note) for note in notes],
        "sites": [_get_site_context(site) for site in sites]
    }
