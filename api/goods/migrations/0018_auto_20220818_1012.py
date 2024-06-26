# Generated by Django 3.2.15 on 2022-08-18 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goods", "0017_good_no_part_number_comments"),
    ]

    operations = [
        migrations.AddField(
            model_name="good",
            name="design_details",
            field=models.TextField(blank=True, default="", help_text="what design details provided", null=True),
        ),
        migrations.AddField(
            model_name="good",
            name="has_declared_at_customs",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="good",
            name="has_security_features",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="good",
            name="security_feature_details",
            field=models.TextField(
                blank=True, default="", help_text="what security features incorporated into the product", null=True
            ),
        ),
    ]
