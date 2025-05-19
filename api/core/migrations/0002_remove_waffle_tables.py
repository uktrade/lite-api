from django.db import migrations


class Migration(migrations.Migration):
    """
    Migration for issue: cannot truncate a table referenced in a foreign key constraint: Table "waffle_flag_groups" references "auth_group".
    See more: https://github.com/django-waffle/django-waffle/issues/317
    """

    dependencies = [
        ("core", "0001_initial"),
        ("waffle", "__latest__"),
    ]

    operations = [
        migrations.RunSQL("DROP TABLE IF EXISTS waffle_flag_groups"),
        migrations.RunSQL("DROP TABLE IF EXISTS waffle_flag_users"),
        migrations.RunSQL("DROP TABLE IF EXISTS waffle_flag"),
    ]
