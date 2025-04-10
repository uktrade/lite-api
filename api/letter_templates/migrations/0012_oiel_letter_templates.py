from django.db import migrations


def populate_oiel_letter_templates(apps, schema_editor):

    CASETYPE_OIEL_ID = "00000000-0000-0000-0000-000000000001"
    APPROVE_DECISION_ID = "00000000-0000-0000-0000-000000000001"
    REFUSE_DECISION_ID = "00000000-0000-0000-0000-000000000003"

    LetterLayout = apps.get_model("letter_layouts", "LetterLayout")
    LetterTemplates = apps.get_model("letter_templates", "LetterTemplate")

    # Create the template and layout
    APPROVAL_LAYOUT_ID = "01353fba-906e-4199-ab18-5f1768a5f736"  # /PS-IGNORE
    REFUSAL_LAYOUT_ID = "dccea004-99cc-4d16-b6f1-16f50d9cc82e"  # /PS-IGNORE
    APPROVAL_LETTER_ID = "81b0c09e-aa96-4590-9393-e1fa09352bb4"
    REFUSAL_LETTER_ID = "b9869e62-547c-4792-b374-c718c3493115"

    oiel_approval_layout, _ = LetterLayout.objects.get_or_create(
        id=APPROVAL_LAYOUT_ID,
        name="OIEL Approval",
        filename="oiel_approval",
    )
    oiel_refusal_layout, _ = LetterLayout.objects.get_or_create(
        id=REFUSAL_LAYOUT_ID, name="OIEL Refusal", filename="oiel_refusal"
    )

    oiel_approval_template, _ = LetterTemplates.objects.get_or_create(
        id=APPROVAL_LETTER_ID,
        name="OIEL Approval",
        layout=oiel_approval_layout,
        visible_to_exporter=True,
        include_digital_signature=True,
    )
    oiel_refusal_template, _ = LetterTemplates.objects.get_or_create(
        id=REFUSAL_LETTER_ID,
        name="OIEL Refusal",
        layout=oiel_refusal_layout,
        visible_to_exporter=True,
        include_digital_signature=True,
    )

    oiel_approval_template.case_types.set([CASETYPE_OIEL_ID])
    oiel_approval_template.decisions.set([APPROVE_DECISION_ID])
    oiel_approval_template.save()

    oiel_refusal_template.case_types.set([CASETYPE_OIEL_ID])
    oiel_refusal_template.decisions.set([REFUSE_DECISION_ID])
    oiel_refusal_template.save()


class Migration(migrations.Migration):

    dependencies = [
        ("letter_templates", "0011_f680_letter_templates"),
    ]

    operations = [
        migrations.RunPython(populate_oiel_letter_templates, migrations.RunPython.noop),
    ]
