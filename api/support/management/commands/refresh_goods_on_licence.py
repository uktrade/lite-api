import logging

from django.core.management.base import BaseCommand

from api.applications.models import StandardApplication
from api.licences import models


class Command(BaseCommand):
    help = """
        Command to update the list of products associated with the given licence reference.

        In some cases users need to edit product attributes after a licence is issued eg serial numbers for firearms
        Currently we don't have a provision to submit updated serial numbers so in this case we can allow the user
        to edit the application, remove previously added product and add the same product again with updated serial
        numbers (same product means the underlying Good should be the same otherwise we lose the advice given and won't
        be able to finalise). In this case user will have to resubmit the application and the licence to be re-issued.
        But this causes issues while finalising it as it will only consider products in the original licence.
        This can be fixed in the advice section but since we are going rewrite that section the fix is done manually
        using this management command.

        First we go through all the products on the application, if the underlying Good is already included in the
        licence then that means it is not edited by the user so we continue. If we find any products that are not on
        the licence then we associate with the licence.

        This will help caseworkers to finalise it from the UI and re-issue new licence. It is to be noted that the
        previously issued licence gets cancelled before we re-issue new one.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "licence_reference", type=str, help="Reference number of the licence generated",
        )

    def handle(self, *args, **options):
        licence_ref = options.pop("licence_reference")
        logging.info(f"Given licence reference is: {licence_ref}")

        try:
            licence = models.Licence.objects.get(reference_code=licence_ref)
        except models.Licence.DoesNotExist:
            logging.error(f"Licence ({licence_ref}) not found, please provide valid licence reference")
            return

        try:
            application = StandardApplication.objects.get(id=licence.case_id)
        except StandardApplication.DoesNotExist:
            logging.error(f"Could not find the matching application for given licence reference")
            return

        product_ids_on_licence = [item.good.good.id for item in licence.goods.all()]

        for index, item in enumerate(application.goods.all(), start=1):
            if item.good.id in product_ids_on_licence:
                logging.info(f"Line item {index} is not edited, continuing ...")
                continue

            logging.info(
                f"Line item {index} with product name {item.good.name} edited by user, associating with the licence"
            )
            good_on_licence = models.GoodOnLicence.objects.create(
                licence=licence, good=item, quantity=item.quantity, value=item.value
            )
            logging.info(
                f"Edited line item {index} with product name {good_on_licence.good.good.name} is now associated with the licence to finalise and re-issue"
            )
