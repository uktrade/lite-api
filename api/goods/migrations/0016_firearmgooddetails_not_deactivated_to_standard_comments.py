# Generated by Django 3.2.13 on 2022-04-27 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goods", "0015_alter_pvgradingdetails_issuing_authority"),
    ]

    operations = [
        migrations.AddField(
            model_name="firearmgooddetails",
            name="not_deactivated_to_standard_comments",
            field=models.TextField(default=""),
        ),
    ]
