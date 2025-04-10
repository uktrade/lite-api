from django.db import migrations


def populate_siel_letter_templates(apps, schema_editor):

    CASETYPE_SIEL_ID = "00000000-0000-0000-0000-000000000004"
    APPROVE_DECISION_ID = "00000000-0000-0000-0000-000000000001"
    REFUSE_DECISION_ID = "00000000-0000-0000-0000-000000000003"
    NLR_DECISION_ID = "00000000-0000-0000-0000-000000000004"

    LetterLayout = apps.get_model("letter_layouts", "LetterLayout")
    LetterTemplates = apps.get_model("letter_templates", "LetterTemplate")

    # Create the template and layout
    APPROVAL_LAYOUT_ID = "00000000-0000-0000-0000-000000000001"  # /PS-IGNORE
    APPROVAL_LETTER_ID = "f689b40d-82cd-462e-82c4-e7e44700f7bd"
    REFUSAL_LAYOUT_ID = "00000000-0000-0000-0000-000000000006"  # /PS-IGNORE
    REFUSAL_LETTER_ID = "dddc0fe2-a869-47d6-8eff-971db490862c"
    NLR_LAYOUT_ID = "00000000-0000-0000-0000-000000000003"
    NLR_LETTER_ID = "e492fabc-976c-48f0-9b75-b5e06aeaeba4"

    # approval
    siel_approval_layout, _ = LetterLayout.objects.get_or_create(
        id=APPROVAL_LAYOUT_ID,
        name="SIEL",
        filename="siel",
    )
    siel_approval_template, _ = LetterTemplates.objects.get_or_create(
        id=APPROVAL_LETTER_ID,
        name="SIEL template",
        layout=siel_approval_layout,
        visible_to_exporter=True,
        include_digital_signature=True,
    )

    # refusal
    siel_refusal_layout, _ = LetterLayout.objects.get_or_create(
        id=REFUSAL_LAYOUT_ID, name="Refusal Letter", filename="refusal"
    )
    siel_refusal_template, _ = LetterTemplates.objects.get_or_create(
        id=REFUSAL_LETTER_ID,
        name="Refusal letter template",
        layout=siel_refusal_layout,
        visible_to_exporter=True,
        include_digital_signature=True,
    )

    # nlr
    nlr_layout, _ = LetterLayout.objects.get_or_create(
        id=NLR_LAYOUT_ID,
        name="No Licence Required Letter",
        filename="nlr",
    )
    nlr_template, _ = LetterTemplates.objects.get_or_create(
        id=NLR_LETTER_ID,
        name="No licence required letter template",
        layout=nlr_layout,
        visible_to_exporter=True,
        include_digital_signature=True,
    )

    siel_approval_template.case_types.set([CASETYPE_SIEL_ID])
    siel_approval_template.decisions.set([APPROVE_DECISION_ID])
    siel_approval_template.save()

    siel_refusal_template.case_types.set([CASETYPE_SIEL_ID])
    siel_refusal_template.decisions.set([REFUSE_DECISION_ID])
    siel_refusal_template.save()

    nlr_template.case_types.set([CASETYPE_SIEL_ID])
    nlr_template.decisions.set([NLR_DECISION_ID])
    nlr_template.save()


class Migration(migrations.Migration):

    dependencies = [
        ("letter_templates", "0012_oiel_letter_templates"),
    ]

    operations = [
        migrations.RunPython(populate_siel_letter_templates, migrations.RunPython.noop),
    ]
