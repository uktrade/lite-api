import logging
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from rest_framework import status, serializers

from applications.models import GoodOnApplication

# from audit_trail import service as audit_trail_service
from cases.enums import CaseTypeEnum
from conf.requests import post
from conf.settings import LITE_HMRC_INTEGRATION_URL, LITE_HMRC_REQUEST_TIMEOUT, HAWK_LITE_API_CREDENTIALS
from licences.models import Licence, HMRCIntegrationUsageUpdate
from licences.serializers.hmrc_integration import HMRCIntegrationLicenceSerializer

SEND_LICENCE_ENDPOINT = "/mail/update-licence/"


class HMRCIntegrationException(Exception):
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


def verify_and_save_licences(validated_data: dict):
    if not HMRCIntegrationUsageUpdate.objects.filter(id=validated_data["transaction_id"]).exists():
        verified_licences = [_verify_licence(licence) for licence in validated_data["licences"]]

        with transaction.atomic():
            licence_ids = [_save_licence(verified_licence) for verified_licence in verified_licences]
            hmrc_integration_usage_update = HMRCIntegrationUsageUpdate.objects.create(
                id=validated_data["transaction_id"]
            )
            hmrc_integration_usage_update.licences.set(licence_ids)


def _verify_licence(validated_licence_data: dict) -> dict:
    """Verifies that a Licence exists and that the Goods exist on that Licence"""

    try:
        licence = Licence.objects.get(id=validated_licence_data["id"])
    except Licence.DoesNotExist:
        raise serializers.ValidationError({"licences": [f"Licence '{validated_licence_data['id']}' not found."]})

    if licence.application.case_type_id in CaseTypeEnum.OPEN_LICENCE_IDS:
        raise serializers.ValidationError(
            {
                "licences": [
                    f"Licence type '{licence.application.case_type.reference}' cannot be updated; "
                    f"Licence '{validated_licence_data['id']}'."
                ]
            }
        )

    validated_licence_data["goods"] = [
        _verify_good_on_licence(licence, validated_good_data) for validated_good_data in validated_licence_data["goods"]
    ]
    return validated_licence_data


def _verify_good_on_licence(validated_licence: Licence, validated_good_data: dict) -> dict:
    """Verifies that a Good exists on a Licence"""

    try:
        validated_good_data["good_on_licence"] = GoodOnApplication.objects.get(
            application=validated_licence.application, good_id=validated_good_data["id"]
        )
    except GoodOnApplication.DoesNotExist:
        raise serializers.ValidationError(
            {"goods": [f"Good '{validated_good_data['id']}' not found on Licence '{validated_licence.id}'"]}
        )

    return validated_good_data


def _save_licence(verified_licence_data: dict) -> UUID:
    """Updates the usages for Goods on a Licence"""

    [_save_usage_update(verified_data) for verified_data in verified_licence_data["goods"]]
    return verified_licence_data["id"]


def _save_usage_update(verified_good_data: dict):
    """Updates the usages for a Good on a Licence"""

    gol = verified_good_data["good_on_licence"]
    gol.usage += verified_good_data["usage"]
    gol.save()

    # audit_trail_service.create_system_user_audit(
    #     verb=AuditType.UPDATED_STATUS, target=gol.application.get_case(), payload={"status": {"new": "", "old": ""}},
    # )
