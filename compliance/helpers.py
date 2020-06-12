import csv

from rest_framework.exceptions import ValidationError

from licences.models import Licence
from lite_content.lite_api.strings import Compliance

TOTAL_COLUMNS = 5


def read_and_validate_csv(text):
    """
    Used for parsing Open Licence returns CSV files which are uploaded by the exporter for certain case types
    and contain the Licence reference as well as other properties for compliance.

    Takes CSV formatted text and returns the licence references & cleaned format of the CSV.
    Requires the first column to be the licence reference.
    Requires 5 items per row or throws a ValidationError.
    Requires the first line to be blank/headers or data will be lost.
    """
    references = set()
    cleaned_text = ""

    try:
        csv_reader = csv.reader(text.split("\n"), delimiter=",")
        # skip headers
        next(csv_reader, None)
        for row in csv_reader:
            if row:
                if len(row) != TOTAL_COLUMNS:
                    raise ValidationError({"file": [Compliance.OpenLicenceReturns.INVALID_FILE_FORMAT]})
                references.add(row[0])
                cleaned_text += ",".join(row) + "\n"
    except csv.Error:
        raise ValidationError({"file": [Compliance.OpenLicenceReturns.INVALID_FILE_FORMAT]})

    return references, cleaned_text


def fetch_and_validate_licences(references, organisation_id):
    if len(references) == 0:
        raise ValidationError({"file": [Compliance.OpenLicenceReturns.INVALID_LICENCES]})

    licence_ids = list(
        Licence.objects.filter(reference_code__in=references, application__organisation_id=organisation_id).values_list(
            "id", flat=True
        )
    )
    if len(licence_ids) != len(references):
        raise ValidationError({"file": [Compliance.OpenLicenceReturns.INVALID_LICENCES]})

    return licence_ids
