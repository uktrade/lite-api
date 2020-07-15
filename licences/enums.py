class HMRCIntegrationActionEnum:
    INSERT = "insert"
    CANCEL = "cancel"
    UPDATE = "update"
    OPEN = "open"
    EXHAUST = "exhaust"
    EXPIRE = "expire"
    SURRENDER = "surrender"

    to_hmrc = [INSERT, CANCEL, UPDATE]
    from_hmrc = [OPEN, EXHAUST, EXPIRE, SURRENDER, CANCEL]


class LicenceStatus:
    ISSUED = "issued"
    REINSTATED = "reinstated"
    REVOKED = "revoked"
    SURRENDERED = "surrendered"
    EXHAUSTED = "exhausted"
    EXPIRED = "expired"
    DRAFT = "draft"
    CANCELLED = "cancelled"

    choices = [
        (ISSUED, "Issued"),
        (ISSUED, "Issued"),
        (REINSTATED, "Reinstated"),
        (REVOKED, "Revoked"),
        (SURRENDERED, "Surrendered"),
        (EXHAUSTED, "Exhausted"),
        (EXPIRED, "Expired"),
        (DRAFT, "Draft"),
        (CANCELLED, "Cancelled"),
    ]

    @classmethod
    def to_str(cls, status):
        return next(choice[1] for choice in cls.choices if choice[0] == status)


hmrc_integration_action_to_licence_status = {
    HMRCIntegrationActionEnum.EXHAUST: LicenceStatus.EXHAUSTED,
    HMRCIntegrationActionEnum.EXPIRE: LicenceStatus.EXPIRED,
    HMRCIntegrationActionEnum.SURRENDER: LicenceStatus.SURRENDERED,
    HMRCIntegrationActionEnum.CANCEL: LicenceStatus.CANCELLED,
}

licence_status_to_hmrc_integration_action = {
    LicenceStatus.ISSUED: HMRCIntegrationActionEnum.INSERT,
    LicenceStatus.REINSTATED: HMRCIntegrationActionEnum.UPDATE,
    LicenceStatus.REVOKED: HMRCIntegrationActionEnum.CANCEL,
    LicenceStatus.SURRENDERED: HMRCIntegrationActionEnum.CANCEL,
    LicenceStatus.EXHAUSTED: HMRCIntegrationActionEnum.CANCEL,
    LicenceStatus.EXPIRED: HMRCIntegrationActionEnum.CANCEL,
    LicenceStatus.CANCELLED: HMRCIntegrationActionEnum.CANCEL,
}
