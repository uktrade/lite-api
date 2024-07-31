import uuid

from django.db import migrations

from api.staticdata.denial_reasons.constants import id_to_uuid_map


def populate_uuid_field(apps, schema_editor):
    DenialReason = apps.get_model("denial_reasons", "DenialReason")
    for denial_reason in DenialReason.objects.all():
        denial_reason.uuid = uuid.UUID(id_to_uuid_map[denial_reason.id])
        denial_reason.save()


class Migration(migrations.Migration):
    dependencies = [
        ("denial_reasons", "0005_denialreason_uuid"),
    ]

    operations = [
        migrations.RunPython(populate_uuid_field, migrations.RunPython.noop),
    ]
