# Generated by Django 2.2.16 on 2020-11-30 01:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goods", "0019_auto_20201127_1123"),
    ]

    operations = [
        migrations.AddField(
            model_name="firearmgooddetails", name="is_sporting_shotgun", field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name="firearmgooddetails", name="has_identification_markings", field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name="firearmgooddetails",
            name="is_covered_by_firearm_act_section_one_two_or_five",
            field=models.BooleanField(null=True),
        ),
    ]
