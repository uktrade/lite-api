# Generated by Django 2.2.16 on 2020-12-07 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0040_goodonapplication_firearm_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="goodonapplication",
            name="is_precedent",
            field=models.BooleanField(default=False),
        ),
    ]
