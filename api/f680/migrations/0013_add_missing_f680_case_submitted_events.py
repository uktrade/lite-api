import logging

from django.db import migrations, transaction

from api.audit_trail.enums import AuditType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.enums import SystemUser

logger = logging.getLogger(__name__)


def add_missing_f680_case_submitted_events(apps, schema_editor):
    Audit = apps.get_model("audit_trail", "Audit")
    F680Application = apps.get_model("f680", "F680Application")

    with transaction.atomic():
        # Audit UPDATED_STATUS was missed as initial release when submitting an f680 applicaion
        # Reporting relies on this event so we added the event back but for the
        # missing data this migration retrospectively adds for the f680 submittion events

        F680Applications = F680Application.objects.all()

        for f680_application in F680Applications:
            Audit.objects.create(
                created_at=f680_application.updated_at,
                updated_at=f680_application.updated_at,
                actor_object_id=SystemUser.id,
                verb=AuditType.UPDATED_STATUS,
                target_object_id=f680_application.id,
                payload={
                    "status": {"new": CaseStatusEnum.SUBMITTED, "old": CaseStatusEnum.DRAFT},
                    "additional_text": "",
                },
            )

            logger.info(
                "Adding %s event for Case reference %s", AuditType.UPDATED_STATUS, f680_application.reference_code
            )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("f680", "0012_recommendation_security_grading_and_more"),
    ]

    operations = [migrations.RunPython(add_missing_f680_case_submitted_events, migrations.RunPython.noop)]
