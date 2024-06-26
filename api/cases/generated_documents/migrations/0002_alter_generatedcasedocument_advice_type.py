# Generated by Django 3.2.20 on 2023-08-21 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("generated_documents", "0001_squashed_0006_generatedcasedocument_licence"),
    ]

    operations = [
        migrations.AlterField(
            model_name="generatedcasedocument",
            name="advice_type",
            field=models.CharField(
                choices=[
                    ("approve", "Approve"),
                    ("proviso", "Proviso"),
                    ("refuse", "Refuse"),
                    ("no_licence_required", "No Licence Required"),
                    ("not_applicable", "Not Applicable"),
                    ("conflicting", "Conflicting"),
                    ("inform", "Inform"),
                ],
                max_length=30,
                null=True,
            ),
        ),
    ]
