import uuid

from django.db import transaction

from api.cases.models import CaseType
from api.staticdata.management.SeedCommand import SeedCommand
from api.letter_templates.models import LetterTemplate


LETTER_TEMPLATES_FILE = "lite_content/lite_api/letter_templates.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedlettertemplates
    """

    help = "Seeds letter templates"
    info = "Seeding letter templates"
    seed_command = "seedlettertemplates"

    @transaction.atomic
    def operation(self, *args, **options):
        if LetterTemplate.objects.exists():
            self.stdout.write(self.style.WARNING("Letter templates already exist, skipping seeding"))
            return

        try:
            csv = self.read_csv(LETTER_TEMPLATES_FILE)
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("Letter templates file does not exist, skipping seeding"))
            return

        case_types = []

        for i, row in enumerate(csv):
            row["id"] = uuid.uuid4()
            row["visible_to_exporter"] = row["visible_to_exporter"] == "true"
            row["include_digital_signature"] = row["include_digital_signature"] == "true"
            case_types.append((row["id"], row.pop("casetype_id")))

        self.update_or_create(LetterTemplate, csv)

        for pk, casetype_id in case_types:
            template = LetterTemplate.objects.get(id=pk)
            template.case_types.add(CaseType.objects.get(pk=casetype_id))
            template.save()
