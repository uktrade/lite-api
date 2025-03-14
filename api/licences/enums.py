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
    SUSPENDED = "suspended"
    EXHAUSTED = "exhausted"
    EXPIRED = "expired"
    DRAFT = "draft"
    CANCELLED = "cancelled"

    choices = [
        (ISSUED, "Issued"),
        (REINSTATED, "Reinstated"),
        (REVOKED, "Revoked"),
        (SURRENDERED, "Surrendered"),
        (SUSPENDED, "Suspended"),
        (EXHAUSTED, "Exhausted"),
        (EXPIRED, "Expired"),
        (DRAFT, "Draft"),
        (CANCELLED, "Cancelled"),
    ]

    open_statuses = [ISSUED, REINSTATED]
    _can_edit_status = [ISSUED, REINSTATED, SUSPENDED]

    @classmethod
    def to_str(cls, status):
        return next(choice[1] for choice in cls.choices if choice[0] == status)

    @classmethod
    def can_edit_status(cls, status):
        return status in cls._can_edit_status

    @classmethod
    def all(cls):
        return [getattr(cls, param) for param in dir(cls) if param.isupper()]  # pragma: no cover


hmrc_integration_action_to_licence_status = {
    HMRCIntegrationActionEnum.SURRENDER: LicenceStatus.SURRENDERED,
    HMRCIntegrationActionEnum.CANCEL: LicenceStatus.CANCELLED,
}

licence_status_to_hmrc_integration_action = {
    LicenceStatus.ISSUED: HMRCIntegrationActionEnum.INSERT,
    LicenceStatus.REINSTATED: HMRCIntegrationActionEnum.UPDATE,
    LicenceStatus.REVOKED: HMRCIntegrationActionEnum.CANCEL,
    LicenceStatus.SURRENDERED: HMRCIntegrationActionEnum.CANCEL,
    LicenceStatus.CANCELLED: HMRCIntegrationActionEnum.CANCEL,
}
