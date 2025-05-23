# Generated by Django 4.2.20 on 2025-05-21 08:44

from django.db import migrations, models, transaction
import django.db.models.deletion


@transaction.atomic
def populate_case_type(apps, schema_editor):
    CaseType = apps.get_model("cases", "CaseType")
    SurveyResponse = apps.get_model("survey", "SurveyResponse")

    case_type_siel = CaseType.objects.get(type="application", sub_type="standard", reference="siel")

    SurveyResponse.objects.filter(user_journey="APPLICATION_SUBMISSION").update(
        case_type=case_type_siel,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0085_add_export_licence_case_type"),
        ("survey", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="surveyresponse",
            name="case_type",
            field=models.ForeignKey(
                blank=True, null=True, default=None, on_delete=django.db.models.deletion.DO_NOTHING, to="cases.casetype"
            ),
        ),
        migrations.RunPython(
            populate_case_type,
            migrations.RunPython.noop,
        ),
    ]
