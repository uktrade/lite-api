from django.db import migrations


def populate_f680_letter_templates(apps, schema_editor):

    CASETYPE_F680_ID = "00000000-0000-0000-0000-000000000007"
    APPROVE_DECISION_ID = "00000000-0000-0000-0000-000000000001"
    REFUSE_DECISION_ID = "00000000-0000-0000-0000-000000000003"

    LetterLayout = apps.get_model("letter_layouts", "LetterLayout")
    LetterTemplates = apps.get_model("letter_templates", "LetterTemplate")

    # Create the template and layout
    APPROVAL_LAYOUT_ID = "8627fbd5-062f-4573-9bdd-b1d80bd8c6bb"  # /PS-IGNORE
    REFUSAL_LAYOUT_ID = "af455bdb-3fa4-41b5-9ff5-ca17d9f94828"  # /PS-IGNORE
    APPROVAL_LETTER_ID = "68a17258-af0f-429e-922d-25945979fa6d"
    REFUSAL_LETTER_ID = "218ed82f-eedb-41bb-9492-ab05b6d04e6f"

    f680_approval_layout, _ = LetterLayout.objects.get_or_create(
        id=APPROVAL_LAYOUT_ID,
        name="F680 Approval",
        filename="f680_approval",
    )
    f680_refusal_layout, _ = LetterLayout.objects.get_or_create(
        id=REFUSAL_LAYOUT_ID, name="F680 Refusal", filename="f680_refusal"
    )

    f680_approval_template, _ = LetterTemplates.objects.get_or_create(
        id=APPROVAL_LETTER_ID,
        name="F680 Approval",
        layout=f680_approval_layout,
        visible_to_exporter=True,
        include_digital_signature=True,
    )
    f680_refusal_template, _ = LetterTemplates.objects.get_or_create(
        id=REFUSAL_LETTER_ID,
        name="F680 Refusal",
        layout=f680_refusal_layout,
        visible_to_exporter=True,
        include_digital_signature=True,
    )

    f680_approval_template.case_types.set([CASETYPE_F680_ID])
    f680_approval_template.decisions.set([APPROVE_DECISION_ID])
    f680_approval_template.save()

    f680_refusal_template.case_types.set([CASETYPE_F680_ID])
    f680_refusal_template.decisions.set([REFUSE_DECISION_ID])
    f680_refusal_template.save()


class Migration(migrations.Migration):

    dependencies = [
        ("letter_templates", "0010_refusal_letter_picklist_update_team_ownership"),
    ]

    operations = [
        migrations.RunPython(populate_f680_letter_templates, migrations.RunPython.noop),
    ]
