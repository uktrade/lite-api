# Generated by Django 3.2.12 on 2022-04-19 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goods", "0012_firearmgooddetails_is_made_before_1938"),
    ]

    operations = [
        migrations.AlterField(
            model_name="firearmgooddetails",
            name="type",
            field=models.TextField(
                choices=[
                    ("firearms", "Firearm"),
                    ("components_for_firearms", "Components for firearms"),
                    ("ammunition", "Ammunition"),
                    ("components_for_ammunition", "Components for ammunition"),
                    ("firearms_accessory", "Accessory of a firearm"),
                    ("software_related_to_firearms", "Software relating to a firearm"),
                    ("technology_related_to_firearms", "Technology relating to a firearm"),
                ]
            ),
        ),
    ]
