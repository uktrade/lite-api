# Generated by Django 4.2.13 on 2024-05-21 13:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("external_data", "0025_entity_type_empty_strings"),
    ]

    operations = [
        migrations.RenameField("Denial", "item_list_codes", "denial_cle"),
        migrations.RenameField("DenialEntity", "item_list_codes", "denial_cle"),
    ]
