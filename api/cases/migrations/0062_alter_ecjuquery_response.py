# Generated by Django 3.2.23 on 2024-01-29 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0061_auto_20240105_1523"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ecjuquery",
            name="response",
            field=models.CharField(blank=True, max_length=2200, null=True),
        ),
    ]