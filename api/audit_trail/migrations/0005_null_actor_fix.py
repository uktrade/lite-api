from django.db import migrations

from api.audit_trail.enums import AuditType
from api.core.constants import Roles


def fill_in_missing_actor(apps, schema_editor):
    if schema_editor.connection.alias != "default":
        return
    ContentType = apps.get_model("contenttypes", "ContentType")
    Audit = apps.get_model("audit_trail", "Audit")
    Case = apps.get_model("cases", "Case")
    UserOrganisationRelationship = apps.get_model("users", "UserOrganisationRelationship")

    for audit in Audit.objects.filter(
        actor_content_type__isnull=True, verb__in=[AuditType.CREATED, AuditType.UPDATED_STATUS]
    ):
        print("Updating audit for:", audit.id)
        case_id = audit.target_object_id or audit.action_object_object_id
        case = Case.objects.get(id=case_id)
        organisation = case.organisation
        admin_relationships = UserOrganisationRelationship.objects.filter(
            organisation=organisation, role=Roles.EXPORTER_SUPER_USER_ROLE_ID,
        ).exclude(user__first_name="")
        user = admin_relationships.first().user
        print("Actor: ", user)
        content_type = ContentType.objects.get(model="exporteruser")
        audit.actor_content_type = content_type
        audit.actor_object_id = user.pk
        print(audit, content_type)
        audit.save()


class Migration(migrations.Migration):
    dependencies = [
        ("applications", "0022_auto_20200331_1107"),
        ("audit_trail", "0004_case_submitted_audits"),
        ("users", "0005_auto_20200322_1547"),
        ("cases", "0013_auto_20200325_1544"),
    ]
    operations = [
        migrations.RunPython(fill_in_missing_actor),
    ]
