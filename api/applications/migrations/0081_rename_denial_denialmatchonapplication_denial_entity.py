# Generated by Django 4.2.13 on 2024-05-29 16:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0080_goodonapplication_report_summaries"),
    ]

    operations = [
        migrations.RenameField(
            model_name="denialmatchonapplication",
            old_name="denial",
            new_name="denial_entity",
        ),
    ]
