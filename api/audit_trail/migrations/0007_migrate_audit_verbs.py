from django.db import migrations

from api.audit_trail.enums import AuditType
from api.audit_trail.payload import audit_type_format


# Verbs that have been changed
DELTA_VERBS = {
    AuditType.MOVE_CASE: "moved the case to: {queues}",
    AuditType.GOOD_REVIEWED: 'good was reviewed: {good_name} control code changed from "{old_control_code}" to "{new_control_code}"',
    AuditType.GRANTED_APPLICATION: "granted licence for {licence_duration} months",
    AuditType.UPDATE_APPLICATION_LETTER_REFERENCE: "updated the letter reference from {old_ref_number} to {new_ref_number}",
}


# Verbs that remain unchanged
EXCLUDED = [AuditType.CREATED]


def migrate_audit_verbs(apps, schema_editor):
    """
    Convert old AuditType.verb with format to new AuditType.verb as enum value.
    """
    if schema_editor.connection.alias != "default":
        return

    Audit = apps.get_model("audit_trail", "Audit")

    total_updates = 0

    for audit_type in AuditType:
        if audit_type in EXCLUDED:
            continue

        old_verb = audit_type_format[audit_type]
        audit_qs = Audit.objects.filter(verb=old_verb)
        count = audit_qs.count()

        if count:
            print({"audit": audit_type.value, "count": count})

        total_updates += count
        audit_qs.update(verb=audit_type)

        if DELTA_VERBS.get(audit_type, False):
            old_audit_qs = Audit.objects.filter(verb=DELTA_VERBS[audit_type])
            count = old_audit_qs.count()

            if count:
                print({"old_audit": audit_type.value, "count": count})

            total_updates += count
            old_audit_qs.update(verb=audit_type)

    if total_updates:
        print({"total_updates": total_updates, "total_audit_count": Audit.objects.exclude(verb__in=EXCLUDED).count()})


class Migration(migrations.Migration):
    dependencies = [
        ("audit_trail", "0006_verb_choices"),
    ]
    operations = [migrations.RunPython(migrate_audit_verbs, migrations.RunPython.noop)]
