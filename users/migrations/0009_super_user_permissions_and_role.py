from django.db import migrations

from conf.constants import Permissions


def create_permission(apps, schema_editor):
    Permission = apps.get_model('users', 'Permission')
    if not Permission.objects.filter(id='ADMINISTER_ROLES'):
        permission = Permission(id='ADMINISTER_ROLES',
                                name='Administer roles')
        permission.save()

    Role = apps.get_model('users', 'Role')
    if not Role.objects.filter(id='00000000-0000-0000-0000-000000000002'):
        role = Role(id='00000000-0000-0000-0000-000000000002',
                    name='Super User')
        role.permissions.set([
            Permissions.MANAGE_FINAL_ADVICE,
            Permissions.MANAGE_TEAM_ADVICE,
            Permissions.REVIEW_GOODS,
            Permissions.ADMINISTER_ROLES
        ])
        role.save()


def remove_permission(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_assess_goods_permission'),
    ]

    operations = [
        migrations.RunPython(create_permission, remove_permission)
    ]
