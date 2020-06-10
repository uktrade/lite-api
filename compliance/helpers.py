import csv

from rest_framework.exceptions import ValidationError

from licences.models import Licence

TOTAL_COLUMNS = 5


def read_and_validate_csv(text):
    references = set()
    cleaned_text = ""

    try:
        csv_reader = csv.reader(text.split("\n"), delimiter=",")
        # skip headers
        next(csv_reader, None)
        for row in csv_reader:
            if row:
                if len(row) != TOTAL_COLUMNS:
                    raise ValidationError({"file": ["Invalid format"]})
                references.add(row[0])
                cleaned_text += ",".join(row) + "\n"
    except csv.Error:
        raise ValidationError({"file": ["Invalid format"]})

    return references, cleaned_text


def fetch_and_validate_licences(references):
    licence_ids = list(Licence.objects.filter(reference_code__in=references).values_list("id", flat=True))
    if len(licence_ids) != len(references) or len(references) == 0:
        raise ValidationError({"file": ["Invalid licence id's"]})

    return licence_ids
