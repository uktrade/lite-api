import logging

from django.core.management.base import BaseCommand

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.applications.helpers import get_application_update_serializer
from api.applications.libraries.get_applications import get_application
from api.cases.models import Case
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.users.models import BaseUser


class Command(BaseCommand):
    help = """
        Command to change the status of a Case.

        This can be changed from UI but not possible for some status values (eg finalised).
        Also when changed from UI the system runs all routing rules but in this case we only
        update the status and not change the routing rules.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "case_reference", type=str, help="Reference number of the application",
        )
        parser.add_argument(
            "status", type=str, help="Required status of the application after update",
        )
        parser.add_argument(
            "--dry_run", action="store_true", help="Print out what action will happen without applying any changes"
        )

    def handle(self, *args, **options):
        case_reference = options.pop("case_reference")
        status = options.pop("status")
        dry_run = options["dry_run"]
        logging.info(f"Given case reference is: {case_reference}")

        try:
            case = Case.objects.get(reference_code=case_reference)
            application = get_application(case.id)
        except Case.DoesNotExist:
            logging.error(f"Case ({case_reference}) not found, please provide valid case reference")
            return

        prev_status = application.status.status
        serializer = get_application_update_serializer(application)
        case_status = get_case_status_by_status(status)
        data = {"status": str(case_status.pk)}
        serializer = serializer(application, data=data, partial=True)
        if not serializer.is_valid():
            logging.error(f"Error updating the status for {case_reference}: {serializer.errors}")
            return

        if not dry_run:
            application = serializer.save()

            system_user = BaseUser.objects.get(id="00000000-0000-0000-0000-000000000001")
            audit_trail_service.create(
                actor=system_user,
                verb=AuditType.UPDATED_STATUS,
                target=application.get_case(),
                payload={"status": {"new": status, "old": prev_status,}, "additional_text": "",},
            )

        logging.info(f"Case {case_reference} status changed from {prev_status} to {status}")
