# Generated by Django 2.2.13 on 2020-07-13 14:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("goodstype", "0004_auto_20200423_1456"),
        ("countries", "0001_initial"),
        ("cases", "0044_convert_good_country_decision"),
    ]

    operations = [
        migrations.RenameField(
            model_name="goodcountrydecision",
            old_name="good",
            new_name="goods_type",
        ),
        migrations.AlterUniqueTogether(
            name="goodcountrydecision",
            unique_together={("case", "goods_type", "country")},
        ),
        migrations.RemoveField(
            model_name="goodcountrydecision",
            name="decision",
        ),
    ]
