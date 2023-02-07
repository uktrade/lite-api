from django.db import migrations


def set_default_govuser_queue(apps, schema_editor):

    GovUser = apps.get_model("users", "GovUser")
    all_cases_system_queue_id = "00000000-0000-0000-0000-000000000001"
    my_assigned_cases_system_queue_id = "00000000-0000-0000-0000-000000000005"
    GovUser.objects.filter(default_queue=my_assigned_cases_system_queue_id).update(
        default_queue=all_cases_system_queue_id
    )


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_exporteruser_external_id"),
    ]

    operations = [migrations.RunPython(set_default_govuser_queue, migrations.RunPython.noop)]
