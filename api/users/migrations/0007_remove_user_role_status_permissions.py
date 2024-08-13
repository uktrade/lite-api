from django.db import migrations


def remove_user_role_status_permissions(apps, schema_editor):
    RoleStatus = apps.get_model("users", "role_statuses")
    RoleStatus.objects.filter(casestatus__status__in=["revoked", "suspended"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_alter_userorganisationrelationship_user"),
    ]

    operations = [migrations.RunPython(remove_user_role_status_permissions, migrations.RunPython.noop)]
