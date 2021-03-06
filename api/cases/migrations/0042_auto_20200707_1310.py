# Generated by Django 2.2.13 on 2020-07-07 13:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0041_casereviewdate"),
    ]

    operations = [
        migrations.AlterField(
            model_name="casenote",
            name="case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="case_notes", to="cases.Case"
            ),
        ),
        migrations.AlterField(
            model_name="casenote",
            name="user",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="case_notes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
