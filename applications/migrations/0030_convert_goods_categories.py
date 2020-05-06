from django.db import migrations


def convert_goods_categories(apps, schema_editor):
    StandardApplication = apps.get_model("applications", "StandardApplication")
    standard_applications = StandardApplication.objects.all()

    for application in standard_applications:
        if application.goods_categories:
            application.contains_firearm_goods = "firearms" in application.goods_categories
            application.goods_categories = None
            application.save()


def reverse_goods_categories(apps, schema_editor):
    StandardApplication = apps.get_model("applications", "StandardApplication")
    standard_applications = StandardApplication.objects.all()

    for application in standard_applications:
        if application.contains_firearm_goods:
            application.goods_categories = "firearms"
        application.contains_firearm_goods = None
        application.save()


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0029_standardapplication_contains_firearm_goods"),
    ]

    operations = [migrations.RunPython(convert_goods_categories, reverse_code=reverse_goods_categories)]
