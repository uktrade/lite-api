from audit_trail.models import Audit
from cases.enums import AdviceLevel, AdviceType
from cases.models import Advice
from conf.helpers import get_date_and_time, add_months, DATE_FORMAT
from licences.models import Licence
from parties.enums import PartyRole


def get_applicant_context(applicant):
    return {"name": " ".join([applicant.first_name, applicant.last_name]), "email": applicant.email}


def get_organisation_context(organisation):
    return {
        "name": organisation.name,
        "eori_number": organisation.eori_number,
        "sic_number": organisation.sic_number,
        "vat_number": organisation.vat_number,
        "registration_number": organisation.registration_number,
        "primary_site": {
            "name": organisation.primary_site.name,
            "address_line_1": organisation.primary_site.address.address_line_1
            or organisation.primary_site.address.address,
            "address_line_2": organisation.primary_site.address.address_line_2,
            "postcode": organisation.primary_site.address.postcode,
            "city": organisation.primary_site.address.city,
            "region": organisation.primary_site.address.region,
            "country": {
                "name": organisation.primary_site.address.country.name,
                "code": organisation.primary_site.address.country.id,
            },
        },
    }


def get_licence_context(licence):
    return {
        "start_date": licence.start_date.strftime(DATE_FORMAT),
        "duration": licence.duration,
        "end_date": add_months(licence.start_date, licence.duration),
    }


def get_party_context(party):
    return {
        "name": party.name,
        "address": party.address,
        "country": {"name": party.country.name, "code": party.country.id,},
        "website": party.website,
    }


def get_third_parties_context(third_parties):
    third_parties_context = {"all": [get_party_context(third_party.party) for third_party in third_parties]}

    # Split third parties into lists based on role
    for role, _ in PartyRole.choices:
        third_parties_of_type = third_parties.filter(party__role=role)
        if third_parties_of_type:
            third_parties_context[role] = [
                get_party_context(third_party.party) for third_party in third_parties_of_type
            ]

    return third_parties_context


def get_good_context(good_on_application, advice):
    good_context = {
        "description": good_on_application.good.description,
        "control_list_entries": [clc.rating for clc in good_on_application.good.control_list_entries.all()],
        "reason": advice.text,
        "note": advice.note,
    }
    if good_on_application.licenced_quantity:
        good_context["quantity"] = good_on_application.licenced_quantity
    if good_on_application.licenced_value:
        good_context["value"] = good_on_application.licenced_value
    if advice.proviso:
        good_context["proviso_reason"] = advice.proviso
    return good_context


def get_goods_context(goods, final_advice):
    final_advice = final_advice.filter(good_id__isnull=False)
    goods_context = {advice_type: [] for advice_type, _ in AdviceType.choices}
    goods_on_application = {good_on_application.good_id: good_on_application for good_on_application in goods.all()}

    for advice in final_advice:
        good_on_application = goods_on_application[advice.good_id]
        goods_context[advice.type].append(get_good_context(good_on_application, advice))

    # Move proviso elements into approved because they are treated the same
    goods_context[AdviceType.APPROVE].extend(goods_context.pop(AdviceType.PROVISO))
    return goods_context


def get_document_context(case):
    date, time = get_date_and_time()
    licence = Licence.objects.filter(application_id=case.pk).order_by("-created_at").first()
    applicant_audit = Audit.objects.filter(target_object_id=case.id).first()
    final_advice = Advice.objects.filter(level=AdviceLevel.FINAL, case_id=case.pk)

    return {
        "reference": case.reference_code,
        "date": date,
        "time": time,
        "applicant": get_applicant_context(applicant_audit.actor) if applicant_audit else None,
        "organisation": get_organisation_context(case.organisation),
        "licence": get_licence_context(licence) if licence else None,
        "end_user": get_party_context(case.end_user.party) if hasattr(case, "end_user") and case.end_user else None,
        "consignee": get_party_context(case.consignee.party) if hasattr(case, "consignee") and case.consignee else None,
        "ultimate_end_users": [
            get_party_context(ultimate_end_user.party) for ultimate_end_user in case.ultimate_end_users
        ]
        if hasattr(case, "ultimate_end_users") and case.ultimate_end_users
        else [],
        "third_parties": get_third_parties_context(case.third_parties)
        if hasattr(case, "third_parties") and case.third_parties
        else [],
        "goods": get_goods_context(case.goods, final_advice) if hasattr(case, "goods") and case.goods else None,
    }
