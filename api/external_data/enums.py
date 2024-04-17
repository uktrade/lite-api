from django.db import models


class DenialMatchCategory:
    PARTIAL = "partial"
    EXACT = "exact"

    choices = [
        (PARTIAL, "Partial"),
        (EXACT, "Exact"),
    ]


class DenialEntityType(models.TextChoices):
    END_USER = "END_USER", "End-user"
    CONSIGNEE = "CONSIGNEE", "Consignee"
    THIRD_PARTY = "THIRD_PARTY", "Third-party"
