import csv

from rest_framework.exceptions import ValidationError


COLUMNS = {"licence_number", "abc"}


def read_and_validate_csv(text):
    licences = set()

    try:
        csv_reader = csv.DictReader(text.split("\n"), delimiter=',')
        for row in csv_reader:
            if set(row.keys()) != COLUMNS:
                raise ValidationError({"file": ["Invalid format"]})
            licences.add(row["licence_number"])
    except Exception:  # noqa
        raise ValidationError({"file": ["Invalid format"]})

    return licences
