import logging

from string import ascii_uppercase

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from api.applications.enums import ApplicationExportType
from api.applications.models import StandardApplication
from api.cases.enums import CaseTypeSubTypeEnum
from api.licences.models import Licence
from api.staticdata.statuses.enums import CaseStatusEnum


class Command(BaseCommand):
    help = "Command to transform application and licence reference to old format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry_run", action="store_true", help="Print out what action will happen without applying any changes"
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        with transaction.atomic():
            for index, application in enumerate(
                StandardApplication.objects.filter(
                    Q(case_type__sub_type=CaseTypeSubTypeEnum.STANDARD)
                    & ~Q(status__status=CaseStatusEnum.DRAFT)
                    & ~Q(reference_code__startswith="GB"),
                ),
                start=1,
            ):
                current_application_reference = application.reference_code
                application_type, serial_number = application.reference_code.split("-")
                application_year = f"20{application_type[3:]}"
                export_type = "P" if application.export_type == ApplicationExportType.PERMANENT else "T"
                reference_old_format = f"GBSIEL/{application_year}/{serial_number}/{export_type}"

                application.reference_code = reference_old_format

                if not dry_run:
                    application.save()

                logging.info(
                    "[%d][%s] Application reference updated from %s to %s",
                    index,
                    application.status.status,
                    current_application_reference,
                    reference_old_format,
                )

            for index, licence in enumerate(Licence.objects.filter(~Q(reference_code__startswith="GB")), start=1):
                current_licence_ref = licence.reference_code
                licence_type, serial_number, version_count = licence.reference_code.split("-")

                application = StandardApplication.objects.get(id=licence.case.id)
                licence_year = f"20{licence_type[3:]}"
                export_type = "P" if application.export_type == ApplicationExportType.PERMANENT else "T"
                version_count = int(version_count)
                licence_reference_old_format = f"GBSIEL/{licence_year}/{serial_number}/{export_type}"
                if version_count > 1:
                    licence_reference_old_format = (
                        f"{licence_reference_old_format}/{ascii_uppercase[version_count - 2]}"
                    )

                licence.reference_code = licence_reference_old_format

                if not dry_run:
                    licence.save()

                logging.info(
                    "[%d][%s] Licence reference updated from %s to %s",
                    index,
                    licence.status,
                    current_licence_ref,
                    licence_reference_old_format,
                )
