# Generated by Django 3.2.16 on 2023-02-01 08:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("statuses", "0004_auto_20210223_1214"),
    ]

    operations = [
        migrations.AddField(
            model_name="casestatus",
            name="next_workflow_status",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to="statuses.casestatus"
            ),
        ),
    ]
