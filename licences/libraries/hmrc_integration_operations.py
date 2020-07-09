import logging
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException

# from audit_trail import service as audit_trail_service
from cases.enums import CaseTypeEnum
from conf.requests import post
from conf.settings import LITE_HMRC_INTEGRATION_URL, LITE_HMRC_REQUEST_TIMEOUT, HAWK_LITE_API_CREDENTIALS
from licences.models import Licence, HMRCIntegrationUsageUpdate, GoodOnLicence
from licences.serializers.hmrc_integration import (
    HMRCIntegrationLicenceSerializer,
    HMRCIntegrationUsageUpdateGoodSerializer,
    HMRCIntegrationUsageUpdateLicenceSerializer,
)

SEND_LICENCE_ENDPOINT = "/mail/update-licence/"


class HMRCIntegrationException(APIException):
    """Exceptions to raise when sending requests to the HMRC Integration service."""


def send_licence(licence: Licence):
    """Sends licence information to HMRC Integration"""

    logging.info(f"Sending licence '{licence.id}' changes to HMRC Integration")

    url = f"{LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}"
    data = {"licence": HMRCIntegrationLicenceSerializer(licence).data}

    response = post(url, data, hawk_credentials=HAWK_LITE_API_CREDENTIALS, timeout=LITE_HMRC_REQUEST_TIMEOUT)

    if response.status_code not in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
        raise HMRCIntegrationException(
            f"An unexpected response was received when sending licence '{licence.id}' changes to HMRC Integration -> "
            f"status={response.status_code}, message={response.text}"
        )

    if response.status_code == status.HTTP_201_CREATED:
        licence.set_sent_at(timezone.now())

    logging.info(f"Successfully sent licence '{licence.id}' changes to HMRC Integration")


def save_licence_usage_updates(usage_update_id: UUID, valid_licences: list):
    """Updates Usage figures on Goods on Licences and creates an HMRCIntegrationUsageUpdate"""

    with transaction.atomic():
        updated_licence_ids = [_update_licence(valid_licence) for valid_licence in valid_licences]
        hmrc_integration_usage_update = HMRCIntegrationUsageUpdate.objects.create(id=usage_update_id)
        hmrc_integration_usage_update.licences.set(updated_licence_ids)


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

    serializer = HMRCIntegrationUsageUpdateLicenceSerializer(data=data)

    if not serializer.is_valid():
        data["errors"] = serializer.errors
        return data

    try:
        licence = Licence.objects.get(id=data["id"])
    except Licence.DoesNotExist:
        data["errors"] = {"id": ["Licence not found."]}
        return data

    if licence.application.case_type_id in CaseTypeEnum.OPEN_LICENCE_IDS:
        data["errors"] = {"id": [f"A '{licence.application.case_type.reference}' Licence cannot be updated."]}
        return data

    valid_goods, invalid_goods = _validate_goods_on_licence(licence.id, data["goods"])

    if invalid_goods:
        data["goods"] = {"accepted": valid_goods, "rejected": invalid_goods}
        data["errors"] = {"goods": ["One or more Goods were rejected."]}

    return data


def _validate_goods_on_licence(licence_id: UUID, goods: list) -> (list, list):
    """Validates that the Goods exist on a Licence"""

    valid_goods = []
    invalid_goods = []

    for good in goods:
        good = _validate_good_on_licence(licence_id, good)

        if not good.get("errors"):
            valid_goods.append(good)
        else:
            invalid_goods.append(good)

    return valid_goods, invalid_goods


def _validate_good_on_licence(licence_id: UUID, data: dict) -> dict:
    """Validates that a Good exists on a Licence"""

    serializer = HMRCIntegrationUsageUpdateGoodSerializer(data=data)
    if not serializer.is_valid():
        data["errors"] = serializer.errors
        return data

    try:
        GoodOnLicence.objects.get(licence_id=licence_id, good__good_id=data["id"])
    except GoodOnLicence.DoesNotExist:
        data["errors"] = {"id": ["Good not found on Licence."]}

    return data


def _update_licence(data: dict) -> UUID:
    """Updates the Usage for Goods on a Licence"""

    [_update_good_on_licence_usage(data["id"], good["id"], good["usage"]) for good in data["goods"]]
    return data["id"]


def _update_good_on_licence_usage(licence_id: UUID, good_id: UUID, usage: int):
    """Updates the Usage for a Good on a Licence"""

    GoodOnLicence.objects.filter(licence_id=licence_id, good__good_id=good_id).update(usage=usage)

    # audit_trail_service.create_system_user_audit(
    #     verb=AuditType.UPDATED_STATUS, target=gol.application.get_case(), payload={"status": {"new": "", "old": ""}},
    # )
