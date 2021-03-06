# Generated by Django 2.2.10 on 2020-03-03 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0006_auto_20200225_1128"),
    ]

    operations = [
        migrations.AddField(
            model_name="advice",
            name="collated_pv_grading",
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="advice",
            name="pv_grading",
            field=models.CharField(
                choices=[
                    ("uk_unclassified", "UK UNCLASSIFIED"),
                    ("uk_official", "UK OFFICIAL"),
                    ("uk_official_sensitive", "UK OFFICIAL - SENSITIVE"),
                    ("uk_secret", "UK SECRET"),
                    ("uk_top_secret", "UK TOP SECRET"),
                    ("nato_unclassified", "NATO UNCLASSIFIED"),
                    ("nato_confidential", "NATO CONFIDENTIAL"),
                    ("nato_restricted", "NATO RESTRICTED"),
                    ("nato_secret", "NATO SECRET"),
                    ("occar_unclassified", "OCCAR UNCLASSIFIED"),
                    ("occar_confidential", "OCCAR CONFIDENTIAL"),
                    ("occar_restricted", "OCCAR RESTRICTED"),
                    ("occar_secret", "OCCAR SECRET"),
                ],
                max_length=30,
                null=True,
            ),
        ),
    ]
