import logging
import urllib
from uuid import UUID

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException
from django.conf import settings

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enums import CaseTypeEnum
from api.core.requests import get, post
from api.licences.enums import HMRCIntegrationActionEnum
from api.licences.helpers import get_approved_goods_types
from api.licences.models import Licence, HMRCIntegrationUsageData, GoodOnLicence
from api.licences.serializers.hmrc_integration import (
    HMRCIntegrationLicenceSerializer,
    HMRCIntegrationUsageDataGoodSerializer,
    HMRCIntegrationUsageDataLicenceSerializer,
)


# This is the endpoint used for sending new issued licences
SEND_LICENCE_ENDPOINT = "/mail/update-licence/"


class HMRCIntegrationException(APIException):
    """Exceptions to raise when sending requests to the HMRC Integration service."""

    pass


def send_licence(licence: Licence, action: str):
    """Sends licence information to HMRC Integration"""

    logging.info(f"Sending licence '{licence.id}', action '{action}' to HMRC Integration")

    url = f"{settings.LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}"
    data = {"licence": HMRCIntegrationLicenceSerializer(licence).data}

    response = post(
        url, data, hawk_credentials=settings.HAWK_LITE_API_CREDENTIALS, timeout=settings.LITE_HMRC_REQUEST_TIMEOUT
    )

    if response.status_code not in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
        raise HMRCIntegrationException(
            f"An unexpected response was received when sending licence '{licence.id}', action '{action}' to HMRC "
            f"Integration -> status={response.status_code}, message={response.text}"
        )

    if response.status_code == status.HTTP_201_CREATED:
        licence.hmrc_integration_sent_at = timezone.now()
        licence.save()

    logging.info(f"Successfully sent licence '{licence.id}', action '{action}' to HMRC Integration")


def get_mail_status(licence: Licence):
    """Get mail status for given licence"""

    url_params = urllib.parse.urlencode({"id": licence.reference_code})
    url = f"{settings.LITE_HMRC_INTEGRATION_URL}/mail/licence/?{url_params}"
    response = get(url, hawk_credentials=settings.HAWK_LITE_API_CREDENTIALS, timeout=settings.LITE_HMRC_REQUEST_TIMEOUT)

    if response.status_code != status.HTTP_200_OK:
        raise HMRCIntegrationException(
            f"Got {response.status_code} when trying to get status of licence '{licence.reference_code}'. URL used: '{url}'"
        )

    return response.json()["status"]


def mark_emails_as_processed():
    """Mark emails as processed"""

    url = f"{settings.LITE_HMRC_INTEGRATION_URL}/mail/set-all-to-reply-sent/"
    response = get(url, hawk_credentials=settings.HAWK_LITE_API_CREDENTIALS, timeout=settings.LITE_HMRC_REQUEST_TIMEOUT)

    if response.status_code != status.HTTP_200_OK:
        raise HMRCIntegrationException(
            f"Got {response.status_code} when trying to mark-emails-as-processed. URL used: '{url}'"
        )


def force_mail_push():
    """Force task manager at LITE-HMRC to process queued items (items
    since it's not exactly emails yet)"""

    url = f"{settings.LITE_HMRC_INTEGRATION_URL}/mail/send-licence-updates-to-hmrc/"
    response = get(url, hawk_credentials=settings.HAWK_LITE_API_CREDENTIALS, timeout=settings.LITE_HMRC_REQUEST_TIMEOUT)

    if response.status_code != status.HTTP_200_OK:
        raise HMRCIntegrationException(f"Got {response.status_code} when trying to force-mail-push. URL used: '{url}'")


def save_licence_usage_updates(usage_data_id: UUID, valid_licences: list):
    """Updates Usage figures on Goods on Licences and creates an HMRCIntegrationUsageUpdate"""

    with transaction.atomic():
        updated_licence_ids = [_update_licence(validated_data) for validated_data in valid_licences]
        hmrc_integration_usage_data = HMRCIntegrationUsageData.objects.create(id=usage_data_id)
        hmrc_integration_usage_data.licences.set(updated_licence_ids)


def validate_licence_usage_updates(licences: list) -> (list, list):
    """Validates that Licences exist and that the Goods exist on those Licences"""

    valid_licences = []
    invalid_licences = []

    for licence in licences:
        licence = _validate_licence(licence)

        if not licence.get("errors"):
            valid_licences.append(licence)
        else:
            invalid_licences.append(licence)

    return valid_licences, invalid_licences


def _validate_licence(data: dict) -> dict:
    """Validates that a Licence exists and that the Goods exist on that Licence"""

    serializer = HMRCIntegrationUsageDataLicenceSerializer(data=data)

    if not serializer.is_valid():
        data["errors"] = serializer.errors
        return data

    try:
        licence = Licence.objects.get(id=data["id"])
    except Licence.DoesNotExist:
        data["errors"] = {"id": ["Licence not found."]}
        return data

    if licence.case.case_type_id not in CaseTypeEnum.LICENCE_IDS:
        data["errors"] = {"id": [f"A '{licence.case.case_type.reference}' Licence cannot be updated."]}
        return data

    if data["action"] not in HMRCIntegrationActionEnum.from_hmrc:
        data["errors"] = {"action": [f"Must be one of {HMRCIntegrationActionEnum.from_hmrc}"]}
        return data

    if licence.case.case_type_id not in CaseTypeEnum.OPEN_GENERAL_LICENCE_IDS:
        valid_goods, invalid_goods = _validate_goods_on_licence(licence, data["goods"])

        if invalid_goods:
            data["goods"] = {"accepted": valid_goods, "rejected": invalid_goods}
            data["errors"] = {"goods": ["One or more Goods were rejected."]}

    return data


def _validate_goods_on_licence(licence: Licence, goods: list) -> (list, list):
    """Validates that the Goods exist on a Licence"""

    valid_goods = []
    invalid_goods = []

    for good in goods:
        good = _validate_good_on_licence(licence, good)

        if not good.get("errors"):
            valid_goods.append(good)
        else:
            invalid_goods.append(good)

    return valid_goods, invalid_goods


def _validate_good_on_licence(licence: Licence, data: dict) -> dict:
    """Validates that a Good exists on a Licence"""

    serializer = HMRCIntegrationUsageDataGoodSerializer(data=data)
    if not serializer.is_valid():
        data["errors"] = serializer.errors
        return data

    if licence.case.case_type_id not in CaseTypeEnum.OPEN_LICENCE_IDS:
        gol = GoodOnLicence.objects.filter(licence=licence, good_id=data["id"])
    else:
        gol = get_approved_goods_types(licence.case.baseapplication).filter(id=data["id"])

    if not gol.exists():
        data["errors"] = {"id": ["Good not found on Licence."]}

    return data


def _update_licence(validated_data: dict) -> str:
    """Updates the Usage for Goods on a Licence"""

    licence = Licence.objects.get(id=validated_data["id"])
    [_update_good_on_licence_usage(licence, good["id"], float(good["usage"])) for good in validated_data["goods"]]
    action = validated_data["action"]
    change_status = None
    send_status_change_to_hmrc = False

    if action == HMRCIntegrationActionEnum.EXHAUST:
        change_status = licence.exhaust
    elif action == HMRCIntegrationActionEnum.CANCEL:
        change_status = licence.cancel
    elif action == HMRCIntegrationActionEnum.SURRENDER:
        change_status = licence.surrender
    elif action == HMRCIntegrationActionEnum.EXPIRE:
        change_status = licence.expire

    if (
        action != HMRCIntegrationActionEnum.EXHAUST
        and licence.case.case_type_id in CaseTypeEnum.STANDARD_LICENCE_IDS + CaseTypeEnum.MOD_LICENCE_IDS
    ):
        # If all Goods have been Exhausted; Exhaust the Licence
        if not licence.goods.filter(usage__lt=F("quantity")).exists():
            send_status_change_to_hmrc = action == HMRCIntegrationActionEnum.OPEN
            change_status = licence.exhaust

    if change_status:
        # Changing the licence status will trigger an auditlog entry
        change_status(send_status_change_to_hmrc=send_status_change_to_hmrc)

    return licence.id


def _update_good_on_licence_usage(licence: Licence, validated_good_id: UUID, validated_usage: float):
    """Updates the Usage for a Good on a Licence"""

    if licence.case.case_type_id in CaseTypeEnum.OPEN_LICENCE_IDS:
        gol = get_approved_goods_types(licence.case.baseapplication).get(id=validated_good_id)
        good_description = gol.description
    else:
        gol = GoodOnLicence.objects.get(licence=licence, good_id=validated_good_id)
        good_description = gol.good.good.name or gol.good.good.description

    gol.usage += validated_usage
    gol.save()

    audit_trail_service.create_system_user_audit(
        verb=AuditType.LICENCE_UPDATED_GOOD_USAGE,
        target=licence.case,
        payload={"good_description": good_description, "usage": gol.usage, "licence": licence.reference_code},
    )
