import csv


def get_ela_report():

    headers = [
        "DATE_SUBMITTED",
        "CASE_CLOSED_DATETIME",
        "TOTAL_DAYS",
        "Case Amendment True/False or Y/N",
        "REVIEW_DAYS",
        "DIT_DAYS",
        "GOODS RATING",
        "Goods ARS",
        "DTI REF",
        "Licensee",
        "APPLICATION TYPE",
        "INCORPORATION Y/N",
        "END_USER_COUNTRIES",
        "ULTIMATE END USER COUNTRIES",
        "FCO SLA DAYS",
        "MOD SLA DAYS",
        "GCHQ SLA DAYS",
        "DFID SLA DAYS",
        "DECC SLA DAYS",
        "BIS SLA DAYS",
    ]

    objects = []

    for item in records:

        objects.append({
            "DATE_SUBMITTED": application.submitted_at,
            "CASE_CLOSED_DATETIME": application.last_closed_at,
            "TOTAL_DAYS": application.sla_days,
            "Case Amendment True/False or Y/N": ??,
            "REVIEW_DAYS": ??,
            "DIT_DAYS": ??,
            "GOODS RATING": ControlListEntry.objects.filter(good__goods_on_application__application=application).values_list('rating', flat=True),
            "Goods ARS": ??,
            "DTI REF": ??,
            "Licensee": application.organisation.name,
            "APPLICATION TYPE": "{application.case_type.reference} ({application.export_type})",
            "INCORPORATION Y/N": ??,
            "END_USER_COUNTRIES": Party.filter(type=PartyType.END_USER, deleted_at__isnull=True, parties_on_application__application__pk=application).values_list('country', flat=True),
            "ULTIMATE END USER COUNTRIES": Party.filter(type=PartyType.ULTIMATE_END_USER, deleted_at__isnull=True, parties_on_application__application__pk=application).values_list('country', flat=True),,
            "FCO SLA DAYS": None,
            "MOD SLA DAYS": None,
            "GCHQ SLA DAYS": None,
            "DFID SLA DAYS": None,
            "DECC SLA DAYS": None,
            "BIS SLA DAYS": None,
        })

    writer = csv.DictWriter(file_object, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(objects)


