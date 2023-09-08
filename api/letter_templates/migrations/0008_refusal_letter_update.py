from django.db import migrations
from api.picklists.enums import PicklistType


def update_refusal_letter_template_paragraphs(apps, schema_editor):
    PicklistItem = apps.get_model("picklists", "PicklistItem")
    Team = apps.get_model("teams", "Team")

    admin = Team.objects.get(name="Admin")

    with open("lite_content/lite_api/letter_paragraphs/refusal_letter.txt", "r", encoding="utf_8") as f:
        text = f.read()

        PicklistItem.objects.update_or_create(
            team=admin, name="Refusal letter content", type=PicklistType.LETTER_PARAGRAPH, defaults={"text": text}
        )


class Migration(migrations.Migration):
    dependencies = [
        ("letter_templates", "0007_inform_letter_template_update_paragraphs"),
    ]

    operations = [migrations.RunPython(update_refusal_letter_template_paragraphs, migrations.RunPython.noop)]
