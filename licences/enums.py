from enum import Enum


class LicenceStatus(Enum):
    ISSUED = "issued"
    REINSTATED = "reinstated"
    REVOKED = "revoked"
    SURRENDERED = "surrendered"
    DRAFT = "draft"

    @classmethod
    def values(cls):
        return [tag.value for tag in cls]
