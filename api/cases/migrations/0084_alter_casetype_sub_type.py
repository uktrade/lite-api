# Generated by Django 4.2.19 on 2025-03-21 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0083_alter_casetype_reference"),
    ]

    operations = [
        migrations.AlterField(
            model_name="casetype",
            name="sub_type",
            field=models.CharField(
                choices=[
                    ("standard", "Standard Licence"),
                    ("open", "Open Licence"),
                    ("hmrc", "HMRC Query"),
                    ("end_user_advisory", "End User Advisory Query"),
                    ("goods", "Goods Query"),
                    ("exhibition_clearance", "MOD Exhibition Clearance"),
                    ("gifting_clearance", "MOD Gifting Clearance"),
                    ("f680_clearance", "MOD F680 Clearance"),
                    ("compliance_site", "Compliance Site Case"),
                    ("compliance_visit", "Compliance Visit Case"),
                ],
                max_length=35,
                null=True,
            ),
        ),
    ]
