class HMRCIntegrationActionEnum:
    INSERT = "insert"
    CANCEL = "cancel"
    UPDATE = "update"


class LicenceStatus:
    ISSUED = "issued"
    REINSTATED = "reinstated"
    REVOKED = "revoked"
    SURRENDERED = "surrendered"
    SUSPENDED = "suspended"
    DRAFT = "draft"
    CANCELLED = "cancelled"

    choices = [
        (ISSUED, "Issued"),
        (REINSTATED, "Reinstated"),
        (REVOKED, "Revoked"),
        (SURRENDERED, "Surrendered"),
        (SUSPENDED, "Suspended"),
        (DRAFT, "Draft"),
        (CANCELLED, "Cancelled"),
    ]

    hmrc_integration_action = {
        ISSUED: HMRCIntegrationActionEnum.INSERT,
        REINSTATED: HMRCIntegrationActionEnum.UPDATE,
        REVOKED: HMRCIntegrationActionEnum.CANCEL,
        SUSPENDED: HMRCIntegrationActionEnum.CANCEL,
        SURRENDERED: HMRCIntegrationActionEnum.CANCEL,
        CANCELLED: HMRCIntegrationActionEnum.CANCEL,
    }

    @classmethod
    def to_str(cls, status):
        return next(choice[1] for choice in cls.choices if choice[0] == status)
