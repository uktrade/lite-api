# Generated by Django 3.1.7 on 2021-02-22 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("external_data", "0011_auto_20210129_1310"),
    ]

    operations = [
        migrations.AlterField(
            model_name="denial",
            name="data",
            field=models.JSONField(default=dict),
        ),
    ]
