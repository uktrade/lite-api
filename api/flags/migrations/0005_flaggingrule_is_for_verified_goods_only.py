# Generated by Django 2.2.11 on 2020-04-02 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flags", "0004_auto_20200326_1548"),
    ]

    operations = [
        migrations.AddField(
            model_name="flaggingrule",
            name="is_for_verified_goods_only",
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
