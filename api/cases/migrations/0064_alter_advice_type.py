# Generated by Django 4.2.11 on 2024-04-04 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0063_ecjuquery_chaser_email_sent_on"),
    ]

    operations = [
        migrations.AlterField(
            model_name="advice",
            name="type",
            field=models.CharField(
                choices=[
                    ("approve", "Approve"),
                    ("proviso", "Proviso"),
                    ("refuse", "Refuse"),
                    ("no_licence_required", "No Licence Required"),
                    ("not_applicable", "Not Applicable"),
                    ("conflicting", "Conflicting"),
                    ("inform", "Inform"),
                    ("f680", "F680"),
                ],
                max_length=30,
            ),
        ),
    ]