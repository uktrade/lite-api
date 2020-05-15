import datetime

from django.utils import timezone

from licences.models import Licence


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
            "address_line_1": organisation.primary_site.address.address_line_1 or organisation.primary_site.address.address,
            "address_line_2": organisation.primary_site.address.address_line_2,
            "postcode": organisation.primary_site.address.postcode,
            "city": organisation.primary_site.address.city,
            "region": organisation.primary_site.address.region,
            "country": {
                "name": organisation.primary_site.address.country.name,
                "code":  organisation.primary_site.address.country.id,
            }
        }
    }


def get_licence_context(licence):
    return {
        "start_date": licence.start_date.strftime(DATE_FORMAT),
        "duration": licence.duration,
        "end_date": add_months(licence.start_date, licence.duration)
    }


def get_document_context(case):
    date, time = get_date_and_time()
    licence = Licence.objects.filter(application_id=case.pk).order_by("-created_at").first()

    return {
        "reference": case.reference_code,
        "date": date,
        "time": time,
        "organisation": get_organisation_context(case.organisation),
        "licence": get_licence_context(licence),
    }
