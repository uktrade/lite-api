# Generated by Django 3.2.15 on 2022-08-24 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("routing_rules", "0001_squashed_0003_auto_20201229_1454"),
        ("lite_routing", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="routingrule",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="routingrule",
            name="is_python_criteria",
            field=models.BooleanField(default=False),
        ),
    ]
