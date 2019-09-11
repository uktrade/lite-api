from django.db import migrations

from static.statuses.enums import CaseStatusEnum


def populate_statuses(apps, schema_editor):
    CaseStatus = apps.get_model('statuses', 'CaseStatus')
    CaseStatus.objects.all().delete()

    for choice in CaseStatusEnum.choices:
        case_status = CaseStatus(status=choice[0], priority=CaseStatusEnum.priorities[choice[0]])
        case_status.save()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('statuses', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_statuses),
    ]
