from django.db import migrations
from api.picklists.enums import PicklistType


def update_refusal_letter_template_paragraphs_fix(apps, schema_editor):
    PicklistItem = apps.get_model("picklists", "PicklistItem")
    Team = apps.get_model("teams", "Team")

    admin = Team.objects.get(name="Admin")
    record = PicklistItem.objects.filter(
        text__iexact="Dear,\r\n\r\nHaving carefully considered your application, an export licence has been refused for the goods listed in the attached schedule. If you would like further information about the decision, please contact Jeanette Rosenberg at jeanette.rosenberg@trade.gov.uk, (tel: 07917 751 668).\r\n\r\nYou may appeal against this decision, but you must do so in writing within 28 calendar days of the date of this refusal letter. In doing so you must provide argument or information that was not available to us at the time of refusal, and which could materially affect the decision to refuse.\r\n\r\nAppeal letters should be sent by email to Colin Baker at colin.baker@trade.gov.uk. If you have any questions about the progress of your appeal, please contact Colin (tel: 07391 864 815).\r\n\r\nFor licence applications refused under the Strategic Export Licensing Criteria more information is available at:\r\nhttps://questions-statements.parliament.uk/written-statements/detail/2021-12-08/hcws449.\r\n\r\nYours sincerely,\r\n\r\nExport Control Joint Unit"
    )
    if record:
        PicklistItem.objects.filter(name="Refusal letter content").exclude(id=record.first().id).delete()

    with open("lite_content/lite_api/letter_paragraphs/refusal_letter.txt", "r", encoding="utf_8") as f:
        text = f.read()

        PicklistItem.objects.update_or_create(
            team=admin, name="Refusal letter content", type=PicklistType.LETTER_PARAGRAPH, defaults={"text": text}
        )


class Migration(migrations.Migration):
    dependencies = [
        ("letter_templates", "0008_refusal_letter_update"),
    ]

    operations = [migrations.RunPython(update_refusal_letter_template_paragraphs_fix, migrations.RunPython.noop)]
