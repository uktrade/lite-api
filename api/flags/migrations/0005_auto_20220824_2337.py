# Generated by Django 3.1.8 on 2022-08-24 22:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flags", "0004_populate_system_alias_flags"),
    ]

    operations = [
        migrations.AddField(
            model_name="flaggingrule",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="flaggingrule",
            name="is_python_criteria",
            field=models.BooleanField(default=False),
        ),
    ]
