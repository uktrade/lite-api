# Generated by Django 3.1.14 on 2022-01-25 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flags", "0002_auto_20210518_1615"),
    ]

    operations = [
        migrations.AddField(
            model_name="flag",
            name="alias",
            field=models.TextField(default=None, null=True, unique=True, help_text="fixed static field for reference"),
        ),
    ]
