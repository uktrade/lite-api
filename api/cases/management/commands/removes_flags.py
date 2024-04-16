from django.core.management.base import BaseCommand
from api.cases.libraries.finalise import remove_flags_on_finalisation, remove_flags_from_audit_trail
from api.cases.models import Case
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.statuses.enums import CaseStatusEnum


class Command(BaseCommand):
    help = "Flags to be removed from Case and Audit Trails"

    def handle(self, *args, **options):
        count = 0
        withdrawn_status = CaseStatus.objects.get(status=CaseStatusEnum.WITHDRAWN)
        finalised_status = CaseStatus.objects.get(status=CaseStatusEnum.FINALISED)

        for case in Case.objects.all():
            if case.status == finalised_status or case.status == withdrawn_status:
                remove_flags_on_finalisation(case)
                remove_flags_from_audit_trail(case)
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully adjusted {count} cases."))
