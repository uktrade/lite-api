# Generated by Django 4.2.15 on 2024-09-13 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("control_list_entries", "0005_adds_5D001e"),
    ]

    operations = [
        migrations.AddField(
            model_name="controllistentry",
            name="selectable_for_assessment",
            field=models.BooleanField(default=True),
        ),
    ]