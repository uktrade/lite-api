# Generated by Django 3.2.15 on 2022-08-26 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goods", "0018_auto_20220818_1012"),
    ]

    operations = [
        migrations.AddField(
            model_name="good",
            name="product_description",
            field=models.TextField(blank=True, default="", null=True),
        ),
    ]
