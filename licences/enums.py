class LicenceStatus:
    ISSUED = "issued"
    REINSTATED = "reinstated"
    REVOKED = "revoked"
    SURRENDERED = "surrendered"
    DRAFT = "draft"
    CANCELLED = "cancelled"

    choices = [
        (ISSUED, "Issued"),
        (REINSTATED, "Reinstated"),
        (REVOKED, "Revoked"),
        (SURRENDERED, "Surrendered"),
        (DRAFT, "Draft"),
        (CANCELLED, "Cancelled"),
    ]

    @classmethod
    def human_readable(cls, status):
        return next(choice[1] for choice in cls.choices if choice[0] == status)
