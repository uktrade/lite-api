import logging

from datetime import datetime

from django.db import migrations, transaction
from django.db.models import Q

from api.audit_trail.enums import AuditType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.enums import SystemUser

logger = logging.getLogger(__name__)


def add_missing_case_updated_status_events(apps, schema_editor):
    Audit = apps.get_model("audit_trail", "Audit")
    Case = apps.get_model("cases", "Case")

    with transaction.atomic():
        # Audit UPDATED_STATUS was removed as part of Notes and timeline changes
        # and for the dates below this event is not emitted when a case is finalised.
        # Reporting relies on this event so we added the event back but for the
        # missing data this migration retrospectively adds for the cases finalised
        # between these dates.
        start_date = datetime.strptime("28-06-2022", "%d-%m-%Y")
        end_date = datetime.strptime("20-08-2022", "%d-%m-%Y")

        system_user_event = Audit.objects.filter(actor_object_id=SystemUser.id).last()

        finalised_cases_events = Audit.objects.filter(
            Q(created_at__date__gte=start_date)
            & Q(created_at__date__lte=end_date)
            & Q(verb=AuditType.CREATED_FINAL_RECOMMENDATION)
        )

        for event in finalised_cases_events:
            case = Case.objects.get(id=event.target_object_id)
            Audit.objects.create(
                created_at=event.created_at,
                updated_at=event.updated_at,
                actor_object_id=SystemUser.id,
                actor_content_type=system_user_event.actor_content_type,
                verb=AuditType.UPDATED_STATUS,
                target_object_id=event.target_object_id,
                target_content_type=event.target_content_type,
                payload={
                    "status": {"new": CaseStatusEnum.FINALISED, "old": CaseStatusEnum.UNDER_FINAL_REVIEW},
                    "additional_text": "",
                },
            )

            logger.info("Adding %s event for Case reference %s", AuditType.UPDATED_STATUS, case.reference_code)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("audit_trail", "0011_auto_20220628_0702"),
    ]

    operations = [migrations.RunPython(add_missing_case_updated_status_events, migrations.RunPython.noop)]
