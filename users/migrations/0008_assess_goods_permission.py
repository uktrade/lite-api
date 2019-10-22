from django.db import migrations, models

from goods.models import Good
from queries.control_list_classifications.models import ControlListClassificationQuery


def create_permission(apps, schema_editor):
    Permission = apps.get_model('users', 'Permission')
    if not Permission.objects.filter(id='REVIEW_GOODS'):
        permission = Permission(id='REVIEW_GOODS',
                                name='Review goods')
        permission.save()


def remove_permission(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_delete_govuserrevisionmeta'),
        ('cases', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_permission, remove_permission)
    ]
