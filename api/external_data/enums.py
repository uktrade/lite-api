from django.db import models


class DenialMatchCategory:
    PARTIAL = "partial"
    EXACT = "exact"

    choices = [
        (PARTIAL, "Partial"),
        (EXACT, "Exact"),
    ]


class DenialEntityType(models.TextChoices):
    end_user = "End-user"
    consignee = "Consignee"
    third_party = "Third-party"
