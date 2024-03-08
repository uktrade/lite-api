# Generated by Django 4.2.9 on 2024-02-29 16:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0077_back_populate_product_report_summary_prefix_and_suffix"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="f680clearanceapplication",
            name="baseapplication_ptr",
        ),
        migrations.RemoveField(
            model_name="f680clearanceapplication",
            name="types",
        ),
        migrations.RemoveField(
            model_name="giftingclearanceapplication",
            name="baseapplication_ptr",
        ),
        migrations.RemoveField(
            model_name="hmrcquery",
            name="baseapplication_ptr",
        ),
        migrations.RemoveField(
            model_name="hmrcquery",
            name="hmrc_organisation",
        ),
        migrations.DeleteModel(
            name="ExhibitionClearanceApplication",
        ),
        migrations.DeleteModel(
            name="F680ClearanceApplication",
        ),
        migrations.DeleteModel(
            name="GiftingClearanceApplication",
        ),
        migrations.DeleteModel(
            name="HmrcQuery",
        ),
    ]