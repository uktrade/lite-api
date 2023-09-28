from django.core.management.base import BaseCommand, CommandError

from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import Advice
from api.staticdata.denial_reasons.models import DenialReason


class Command(BaseCommand):
    help = "Convert final Advice of type 'no_licence_required' to type 'refuse'."

    def add_arguments(self, parser):
        parser.add_argument("advice_ids", nargs="+", type=str)
        parser.add_argument(
            "--case_reference",
            action="store",
            required=True,
            help="The case reference for the advice to modify",
        )
        parser.add_argument(
            "--text",
            action="store",
            required=True,
            help="The text to save on the modified advice records",
        )
        parser.add_argument(
            "--denial_reasons",
            action="store",
            required=True,
            nargs="+",
            help="The text to save on the modified advice records",
        )

    def handle(self, *args, **options):

        advice_objects_to_update = Advice.objects.filter(
            id__in=options["advice_ids"],
            case__reference_code=options["case_reference"],
            type=AdviceType.NO_LICENCE_REQUIRED,
            level=AdviceLevel.FINAL,
        )
        expected_advice_count = len(options["advice_ids"])
        advice_count = advice_objects_to_update.count()
        if advice_count != expected_advice_count:
            raise CommandError(f"Expected to find {expected_advice_count} Advice records but found {advice_count}")

        denial_reasons = DenialReason.objects.filter(id__in=options["denial_reasons"])
        expected_denial_reason_count = len(options["denial_reasons"])
        denial_reason_count = denial_reasons.count()
        if denial_reason_count != expected_denial_reason_count:
            raise CommandError(
                f"Expected to find {expected_denial_reason_count} DenialReason records but found {denial_reason_count}"
            )

        new_values = {
            "type": "refuse",
            "text": options["text"],
            "is_refusal_note": True,
            "denial_reasons": denial_reasons,
        }

        for advice in advice_objects_to_update:
            advice.type = new_values["type"]
            advice.text = new_values["text"]
            advice.is_refusal_note = new_values["is_refusal_note"]
            advice.save()
            advice.denial_reasons.add(*list(new_values["denial_reasons"]))

        self.stdout.write(self.style.SUCCESS(f"Successfully adjusted {advice_count} Advice records"))
