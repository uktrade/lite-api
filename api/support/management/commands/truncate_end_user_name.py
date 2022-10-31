import logging

from rest_framework import status

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from api.core.requests import post
from api.licences.models import Licence
from api.licences.serializers.hmrc_integration import HMRCIntegrationLicenceSerializer
from api.licences.libraries.hmrc_integration_operations import HMRCIntegrationException, SEND_LICENCE_ENDPOINT


class Command(BaseCommand):
    help = """
    Command to truncate End-user name (to 80 chars) and sends licence details to HMRC

    This is required because HMRC spec allows only 80 chars otherwise we won't be able to
    send licence details to HMRC
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "licence_reference",
            type=str,
            help="Reference number of the licence generated",
        )

    def handle(self, *args, **options):
        licence_ref = options.pop("licence_reference")
        logging.info("Given licence reference is: %s", licence_ref)

        with transaction.atomic():
            try:
                licence = Licence.objects.get(reference_code=licence_ref)
            except Licence.DoesNotExist:
                logging.error("Licence (%s) not found, please provide valid licence reference", licence_ref)
                return

            data = {"licence": HMRCIntegrationLicenceSerializer(licence).data}
            end_user = data["licence"]["end_user"]
            if len(end_user["name"]) <= 80:
                logging.info("End-user name already <= 80 chars, returning ...")
                return

            # HMRC spec allows only 80 chars
            end_user["name"] = end_user["name"][:80]

            data["licence"]["end_user"] = end_user
            url = f"{settings.LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}"

            response = post(
                url,
                data,
                hawk_credentials=settings.HAWK_LITE_API_CREDENTIALS,
                timeout=settings.LITE_HMRC_REQUEST_TIMEOUT,
            )

            if response.status_code not in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
                raise HMRCIntegrationException(
                    f"An unexpected response was received when sending licence '{licence.id}', action INSERT to HMRC "
                    f"Integration -> status={response.status_code}, message={response.text}"
                )

            if response.status_code == status.HTTP_201_CREATED:
                licence.hmrc_integration_sent_at = timezone.now()
                licence.save()

            logging.info(f"Successfully sent licence '{licence.reference_code}', action INSERT to HMRC Integration")
