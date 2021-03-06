# Generated by Django 2.2.11 on 2020-03-26 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("addresses", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="address",
            name="address",
            field=models.CharField(
                blank=True, default=None, help_text="Used for addresses not in the UK", max_length=256, null=True
            ),
        ),
        migrations.AlterField(
            model_name="address",
            name="address_line_1",
            field=models.CharField(blank=True, default=None, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="address",
            name="address_line_2",
            field=models.CharField(blank=True, default=None, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="address", name="city", field=models.CharField(default=None, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="address",
            name="postcode",
            field=models.CharField(blank=True, default=None, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name="address",
            name="region",
            field=models.CharField(blank=True, default=None, max_length=50, null=True),
        ),
        migrations.AlterModelTable(name="address", table="address",),
    ]
