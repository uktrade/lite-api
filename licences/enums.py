from enum import Enum


class LicenceStatus(Enum):
    ISSUED = "issued"
    REINSTATED = "reinstated"
    REVOKED = "revoked"
    SURRENDERED = "surrendered"
    DRAFT = "draft"
    CANCELLED = "cancelled"
    REFUSED = "refused"
    NOT_REQUIRED = "not_required"

    @classmethod
    def values(cls):
        return [tag.value for tag in cls]

    @classmethod
    def human_readable(cls, status):
        status = cls(status)
        return {
            cls.ISSUED: "Issued",
            cls.REINSTATED: "Reinstated",
            cls.REVOKED: "Revoked",
            cls.SURRENDERED: "Surrendered",
            cls.DRAFT: "Draft",
            cls.CANCELLED: "Cancelled",
            cls.REFUSED: "Refused",
            cls.NOT_REQUIRED: "Not Required",
        }[status]
