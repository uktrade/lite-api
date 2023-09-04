import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from api.applications.models import StandardApplication
from api.applications.views.helpers.advice import remove_countersign_process_flags
from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import Case
from api.queues.models import Queue

from lite_routing.routing_rules_internal.enums import QueuesEnum

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
        Command to delete Refusal advice given by LU on a refused Case.

        When an application is refused licence then Exporters have an option to appeal.
        If an appeal is valid then ECJU may consider it. In some cases this may result
        in overturning of the original refusal decision and they may decide the issue
        a licence. In this case this command is helpful to remove previous refusal
        advice given by LU so that they can now approve and finalise the case again
        to issue a licence. Since these cases are very rare this functionality is  not
        part of LITE and management command is provided to automate in such cases.
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
            except Case.DoesNotExist:
                logger.error("Invalid Case reference %s, does not exist", case_reference)
                return

            # Ensure final advice given by LU is refusal
            final_advice = case.advice.filter(level=AdviceLevel.FINAL, type=AdviceType.REFUSE)
            if not final_advice.exists():
                logger.error("Invalid Advice data, LU not refused the Case")
                return

            if not dry_run:
                # Move the Case to 'LU Post-Circulation Cases to Finalise' queue
                # as it needs to be in this queue to finalise and issue
                case.queues.set(Queue.objects.filter(id=QueuesEnum.LU_POST_CIRC))

                for item in final_advice:
                    item.delete()

                # Remove countersigning flags if any
                # Since this is a refusal we would've already removed these flags when
                # it was refused initially but flagging rules would've applied them
                # again when Case status is changed during Appeals process.
                #
                # If there are no flags then this does nothing.
                application = StandardApplication.objects.get(id=case.id)
                remove_countersign_process_flags(application, case)

            logging.info("[%s] can now be finalised by LU to issue a licence", case_reference)
