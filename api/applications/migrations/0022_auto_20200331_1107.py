# Generated by Django 2.2.11 on 2020-03-31 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0021_baseapplication_agreed_to_foi"),
    ]

    operations = [
        migrations.AddField(
            model_name="openapplication",
            name="is_temp_direct_control",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="openapplication",
            name="proposed_return_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="openapplication",
            name="temp_direct_control_details",
            field=models.CharField(blank=True, default=None, max_length=2200, null=True),
        ),
        migrations.AddField(
            model_name="openapplication",
            name="temp_export_details",
            field=models.CharField(blank=True, default=None, max_length=2200, null=True),
        ),
        migrations.AddField(
            model_name="standardapplication",
            name="is_temp_direct_control",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="standardapplication",
            name="proposed_return_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="standardapplication",
            name="temp_direct_control_details",
            field=models.CharField(blank=True, default=None, max_length=2200, null=True),
        ),
        migrations.AddField(
            model_name="standardapplication",
            name="temp_export_details",
            field=models.CharField(blank=True, default=None, max_length=2200, null=True),
        ),
    ]
