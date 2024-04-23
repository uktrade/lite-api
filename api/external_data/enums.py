class DenialMatchCategory:
    PARTIAL = "partial"
    EXACT = "exact"

    choices = [
        (PARTIAL, "Partial"),
        (EXACT, "Exact"),
    ]


class DenialEntityType:
    CONSIGNEE = "consignee"
    END_USER = "end_user"
    THIRD_PARTY = "third_party"

    choices = ((CONSIGNEE, "Consignee"), (END_USER, "End-user"), (THIRD_PARTY, "Third party"))
