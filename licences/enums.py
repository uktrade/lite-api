from common.enums import LiteEnum, autostr


class LicenceStatus(LiteEnum):
    ISSUED = autostr()
    REINSTATED = autostr()
    REVOKED = autostr()
    SURRENDERED = autostr()
    DRAFT = autostr()

    @classmethod
    def values(cls):
        return [tag.value for tag in cls]
