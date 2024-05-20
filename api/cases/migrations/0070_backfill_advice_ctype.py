# -*- coding: utf-8 -*-
from django.db import migrations, models


def forwards_func(apps, schema_editor):
    BaseAdvice = apps.get_model("cases", "BaseAdvice")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Advice = apps.get_model("cases", "Advice")

    new_ct = ContentType.objects.get_for_model(Advice)
    BaseAdvice.objects.all().update(polymorphic_ctype=new_ct)


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0001_initial"),
        ("cases", "0069_remove_advice_case_remove_advice_created_at_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
