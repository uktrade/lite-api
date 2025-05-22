import logging

from django.db import migrations, transaction

from api.audit_trail.enums import AuditType
from api.staticdata.statuses.enums import CaseStatusEnum

logger = logging.getLogger(__name__)


def add_missing_f680_case_submitted_events(apps, schema_editor):
    Audit = apps.get_model("audit_trail", "Audit")
    F680Application = apps.get_model("f680", "F680Application")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Case = apps.get_model("cases", "Case")
    BaseUser = apps.get_model("users", "BaseUser")

    with transaction.atomic():
        # Audit UPDATED_STATUS was missed as initial release when submitting an f680 applicaion
        # Reporting relies on this event so we added the event back but for the
        # missing data this migration retrospectively adds for the f680 submittion events

        F680Applications = F680Application.objects.exclude(status__status=CaseStatusEnum.DRAFT)

        for f680_application in F680Applications:
            base_user = BaseUser.objects.all().first()
            actor_type = ContentType.objects.get_for_model(base_user)

            case = Case.objects.get(id=f680_application.pk)
            content_type = ContentType.objects.get_for_model(case)
            Audit.objects.get_or_create(
                created_at=f680_application.submitted_at,
                updated_at=f680_application.submitted_at,
                actor_object_id=f680_application.submitted_by.pk,
                verb=AuditType.UPDATED_STATUS,
                target_object_id=f680_application.pk,
                actor_content_type=actor_type,
                target_content_type=content_type,
                actor_content_type_id=actor_type.id,
                target_content_type_id=content_type.id,
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
