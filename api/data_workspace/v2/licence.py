from datetime import datetime

from api.licences.enums import LicenceStatus


def is_licence_issued(licence):
    return licence.status == LicenceStatus.ISSUED


def is_licence_valid(licence):
    if not (licence.start_date and licence.end_date):
        return False

    today = datetime.today().date()

    return licence.start_date <= today <= licence.end_date


def is_licence_exhausted(licence):
    """Returns True if all the licenced goods are completely used"""
    used_goods = [
        good_on_licence for good_on_licence in licence.goods.all() if good_on_licence.usage == good_on_licence.quantity
    ]
    return len(used_goods) == licence.goods.count() or licence.status == LicenceStatus.EXHAUSTED


def is_licence_revoked(licence):
    return is_licence_valid and licence.status == LicenceStatus.REVOKED


def is_licence_surrendered(licence):
    return licence.status == LicenceStatus.SURRENDERED


def is_licence_suspended(licence):
    return licence.status == LicenceStatus.SUSPENDED


def is_licence_expired(licence):
    return licence.status == LicenceStatus.EXPIRED or datetime.today().date() > licence.end_date


def is_licence_cancelled(licence):
    return licence.status == LicenceStatus.CANCELLED


def is_licence_extant(licence):

    return (
        licence.status
        in [
            LicenceStatus.ISSUED,
            LicenceStatus.REINSTATED,
        ]
        and is_licence_valid(licence)
        and not is_licence_exhausted(licence)
        and not is_licence_surrendered(licence)
        and not is_licence_expired(licence)
        and not is_licence_revoked(licence)
    )


def determine_licence_status(licence):
    responses = {status: trigger(licence) for status, trigger in licence_status_triggers.items()}

    results = [status for status, value in responses.items() if value is True]
    # Statuses are mutually exclusive so only one result is expected
    if len(results) > 1:
        raise ValueError

    return results[0]


# Status values that are exposed to DW
licence_status_triggers = {
    "extant": is_licence_extant,
    "exhausted": is_licence_exhausted,
    "revoked": is_licence_revoked,
    "surrendered": is_licence_surrendered,
    "suspended": is_licence_suspended,
    "expired": is_licence_expired,
    "cancelled": is_licence_cancelled,
}
