from django.db.models import Min, When, BinaryField, Case

from api.applications.models import CountryOnApplication
from flags.enums import FlagStatuses
from api.users.enums import UserType


def get_destinations(application_id, user_type=None):
    """
    Get destinations for an open application. For gov users they are ordered based on flag priority and alphabetized by name.
    """
    if user_type == UserType.EXPORTER:
        countries_on_application = (
            CountryOnApplication.objects.select_related("country")
            .prefetch_related("flags", "country__flags")
            .filter(application=application_id)
        )
    else:
        countries_on_application = (
            CountryOnApplication.objects.select_related("country")
            .prefetch_related("country__flags", "flags")
            .filter(application=application_id)
            .annotate(
                highest_flag_priority=Min("country__flags__priority"),
                contains_flags=Case(When(country__flags__isnull=True, then=0), default=1, output_field=BinaryField()),
            )
            .order_by("-contains_flags", "highest_flag_priority", "country__name")
        )

    destinations = []

    for coa in countries_on_application:
        destinations.append(
            {
                "id": coa.id,
                "country": {
                    "id": coa.country.id,
                    "name": coa.country.name,
                    "flags": [
                        {"colour": f.colour, "name": f.name, "label": f.label, "id": f.id}
                        for f in coa.country.flags.all()
                        if f.status == FlagStatuses.ACTIVE
                    ],
                },
                "flags": [{"id": f.id, "name": f.name} for f in coa.flags.all()],
                "contract_types": coa.contract_types,
                "other_contract_type_text": coa.other_contract_type_text,
            }
        )

    return {"type": "countries", "data": destinations}
