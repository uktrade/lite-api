import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.audit_trail.enums import AuditType
from api.cases.enums import AdviceLevel
from api.cases.models import Case
from api.queues.models import Queue
from api.audit_trail import service as audit_trail_service

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from lite_routing.routing_rules_internal.enums import QueuesEnum

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
        Command to delete Final advice when a case is ready to finalise

        When an application goes back to TAU and they change their mind we need to
        invalidate all the final advice. This is unsed where cases are ready to proceed
        with finial review. i.e a refusal.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--case_reference",
            type=str,
            nargs="?",
            help="Reference code of the Case (eg GBSIEL/2023/0000001/P)",
        )
        parser.add_argument("--dry_run", help="Is it a test run?", action="store_true")

    def handle(self, *args, **options):
        case_reference = options.pop("case_reference")
        dry_run = options.pop("dry_run")

        with transaction.atomic():
            try:
                case = Case.objects.get(reference_code=case_reference)
            except Case.DoesNotExist as e:
                logger.error("Invalid Case reference %s, does not exist", case_reference)
                raise CommandError(e)

            final_advice = case.advice.filter(level=AdviceLevel.FINAL)

            # Ensure final advice given by LU
            if not final_advice.exists():
                logger.error("Invalid Advice data, no final advice on this case")
                raise CommandError(Exception("Invalid Advice data, no final advice on this case"))

            if not dry_run:
                # Move the Case to 'LU Post-Circulation Cases to Finalise' queue
                # as it needs to be in this queue to finalise and issue
                # also need to ensure the status is under final review.
                case.queues.set(Queue.objects.filter(id=QueuesEnum.LU_POST_CIRC))

                for item in final_advice:
                    item.delete()

                audit_trail_service.create_system_user_audit(
                    verb=AuditType.DEVELOPER_INTERVENTION,
                    target=case,
                    payload={
                        "additional_text": "Removed final advice.",
                    },
                )
                # If the case isn't under final review update the status
                if case.status.status != CaseStatusEnum.UNDER_FINAL_REVIEW:
                    prev_case_status = case.status.status
                    case.status = get_case_status_by_status(CaseStatusEnum.UNDER_FINAL_REVIEW)
                    case.save()
                    audit_trail_service.create_system_user_audit(
                        verb=AuditType.UPDATED_STATUS,
                        target=case,
                        payload={
                            "status": {"new": case.status.status, "old": prev_case_status},
                            "additional_text": "",
                        },
                    )

            logging.info("[%s] can now be finalised by LU to issue a licence", case_reference)
