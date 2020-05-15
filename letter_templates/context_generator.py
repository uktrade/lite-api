import datetime

from django.utils import timezone

from audit_trail.models import Audit
from licences.models import Licence
from parties.enums import PartyRole

DATE_FORMAT = "%D %B %Y"
TIME_FORMAT = "%I:%M %p"


def get_date_and_time():
    now = timezone.now()
    return now.strftime(DATE_FORMAT), now.strftime(TIME_FORMAT)


def add_months(start_date, months):
    year = start_date.year
    month = start_date.month

    for _ in range(months):
        month += 1
        if month == 13:
            year += 1
            month = 1

    new_date = datetime.date(year=year, month=month, day=start_date.day)
    return new_date.strftime(DATE_FORMAT)


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


def get_document_context(case):
    date, time = get_date_and_time()
    licence = Licence.objects.filter(application_id=case.pk).order_by("-created_at").first()
    applicant_audit = Audit.objects.filter(target_object_id=case.id).first()

    return {
        "reference": case.reference_code,
        "date": date,
        "time": time,
        "organisation": get_organisation_context(case.organisation),
        "licence": get_licence_context(licence) if licence else None,
        "end_user": get_party_context(case.end_user.party) if case.end_user else None,
        "consignee": get_party_context(case.consignee.party) if case.consignee else None,
        "ultimate_end_users": [
            get_party_context(ultimate_end_user.party) for ultimate_end_user in case.ultimate_end_users
        ],
        "third_parties": get_third_parties_context(case.third_parties) if case.third_parties else None,
    }
