class LicenceStatus:
    ISSUED = "issued"
    REINSTATED = "reinstated"
    REVOKED = "revoked"
    SURRENDERED = "surrendered"
    DRAFT = "draft"
    CANCELLED = "cancelled"
    REFUSED = "refused"

    choices = [
        (ISSUED, "Issued"),
        (REINSTATED, "Reinstated"),
        (REVOKED, "Revoked"),
        (SURRENDERED, "Surrendered"),
        (DRAFT, "Draft"),
        (CANCELLED, "Cancelled"),
        (REFUSED, "Refused"),
    ]

    @classmethod
    def human_readable(cls, status):
        for key, value in cls.choices:
            if key == status:
                return value
