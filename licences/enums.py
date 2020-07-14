class HMRCIntegrationActionEnum:
    INSERT = "insert"
    CANCEL = "cancel"
    UPDATE = "update"


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

    hmrc_intergration_action = {
        ISSUED: HMRCIntegrationActionEnum.INSERT,
        REINSTATED: HMRCIntegrationActionEnum.UPDATE,
        REVOKED: HMRCIntegrationActionEnum.CANCEL,
        SURRENDERED: HMRCIntegrationActionEnum.CANCEL,
        CANCELLED: HMRCIntegrationActionEnum.CANCEL,
    }

    @classmethod
    def human_readable(cls, status):
        for key, value in cls.choices:
            if key == status:
                return value
