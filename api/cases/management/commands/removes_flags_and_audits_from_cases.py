import logging

from django.db import transaction
from django.db.models import Q

from django.core.management.base import BaseCommand
from api.cases.libraries.finalise import remove_flags_on_finalisation, remove_flags_from_audit_trail
from api.cases.models import Case
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.statuses.enums import CaseStatusEnum

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Command to remove required flags from Cases and Audit Trails for the past cases"

    def handle(self, *args, **options):
        count = 0
        withdrawn_status = CaseStatus.objects.get(status=CaseStatusEnum.WITHDRAWN)
        finalised_status = CaseStatus.objects.get(status=CaseStatusEnum.FINALISED)

        cases = Case.objects.filter(Q(status=withdrawn_status) | Q(status=finalised_status))
        with transaction.atomic():
            for case in cases:
                remove_flags_on_finalisation(case)
                remove_flags_from_audit_trail(case)
                count += 1

            self.stdout.write(self.style.SUCCESS(f"Successfully adjusted {count} cases."))
