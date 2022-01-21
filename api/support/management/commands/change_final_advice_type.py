import logging

from django.core.management.base import BaseCommand

from api.cases.models import Case, AdviceType, AdviceLevel


class Command(BaseCommand):
    help = """
        Command to change the advice type of level 'final' so that all of them are of same type.

        In Advice1.0, all of the advice objects of 'final' level should be of same type either
        'approve' or 'proviso'. If any of them are different then get ignored in the finalise form
        and won't be submitted to the backend to include in the licence.
        
        https://github.com/uktrade/lite-frontend/blob/master/caseworker/templates/components/goods-licence-list.html#L17

        Because of this the application cannot be finalised and API returns below errors for each
        product where advice type is different.

            "You must give a licenced quantity for the good"
            "You must give a value for the good"

        This command accepts case reference and the required advice type. It then goes through each
        product on the application and updates the type if it is different from the required value.

        Please note that NLRs and Refusal types are skipped.

        This is not an issue in Advice2.0 as any recommendation given is for all licenceable goods.

    """

    def add_arguments(self, parser):
        parser.add_argument(
            "case_reference", type=str, help="Case reference of the application",
        )
        parser.add_argument(
            "advice_type", type=str, help="Required type of the advice",
        )

    def handle(self, *args, **options):
        case_reference = options.pop("case_reference")
        advice_type = options.pop("advice_type")
        logging.info(f"Given case reference is: {case_reference}")

        try:
            case = Case.objects.get(reference_code=case_reference)
        except Case.DoesNotExist:
            logging.error(f"Case ({case_reference}) not found, please provide valid Case reference")
            return

        if not bool({advice_type}.intersection({AdviceType.APPROVE, AdviceType.PROVISO})):
            logging.error(f"Advice type ({advice_type}) not found, please provide valid advice type")
            return

        for index, item in enumerate(case.advice.filter(level=AdviceLevel.FINAL, good__isnull=False), start=1):
            if item.type in [AdviceType.NO_LICENCE_REQUIRED, AdviceType.REFUSE]:
                continue

            if item.type != advice_type:
                item.type = advice_type
                item.save()
                logging.info(f"Advice type for line item {index} is updated to {advice_type}")
