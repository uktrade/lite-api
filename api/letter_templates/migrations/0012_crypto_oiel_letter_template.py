from django.db import migrations

from api.cases.enums import CaseTypeEnum


def populate_crypto_oiel_letter_template(apps, schema_editor):

    CASETYPE_OIEL_ID = CaseTypeEnum.OIEL.id
    LICENSING_UNIT_ID = "58e77e47-42c8-499f-a58d-94f94541f8c6"
    ADVICETYPE_APPROVAL_ID = "00000000-0000-0000-0000-000000000001"

    LetterLayout = apps.get_model("letter_layouts", "LetterLayout")
    LetterTemplates = apps.get_model("letter_templates", "LetterTemplate")
    PicklistItem = apps.get_model("picklists", "PicklistItem")
    Team = apps.get_model("teams", "Team")

    lu_team = Team.objects.get(pk=LICENSING_UNIT_ID)

    text = """Dear {{addressee.name}}
    **Application reference: {{ case_reference }}**
    Thank you for your export licence application dated {{case_submitted_at|date:"jS F Y"}}.
    Your crypto OIEL Application has been approved.

    Yours sincerely
    Licensing Unit"""

    pick_list_item = PicklistItem.objects.create(
        team=lu_team,
        name="Crypto OIEL P1",
        text=text,
        type="letter_paragraph",
        status="active",
    )
    pick_list_item.save()

    # Create the template

    crypto_oiel_letter_layout = LetterLayout.objects.create(name="Crypto OIEL Letter", filename="crypto_oiel_letter")
    crypto_oiel_letter_layout.save()

    crypto_oiel_letter_template = LetterTemplates.objects.create(
        name="Crypto OIEL letter",
        layout=crypto_oiel_letter_layout,
        visible_to_exporter=False,
        include_digital_signature=True,
    )

    crypto_oiel_letter_template.letter_paragraphs.set([pick_list_item.id])
    crypto_oiel_letter_template.case_types.set([CASETYPE_OIEL_ID])
    crypto_oiel_letter_template.decisions.set([ADVICETYPE_APPROVAL_ID])
    crypto_oiel_letter_template.save()


class Migration(migrations.Migration):

    dependencies = [
        ("letter_templates", "0011_f680_letter_template_update_advice"),
    ]

    operations = [
        migrations.RunPython(populate_crypto_oiel_letter_template, migrations.RunPython.noop),
    ]
