from django.core.management.base import BaseCommand
from django.db import transaction

from api.goods.enums import FirearmGoodType
from api.goods.models import FirearmGoodDetails


class Command(BaseCommand):
    help = """
        Command to update serial number choices fields data with the existing fields data.

        Current fields to save this data (has_identification_markings) is a boolean but in the
        new form we are providing three options to the User. The safe approach for this is to
        add a new field, update the data with the existing field's data using this management
        command and finally delete the existing field
    """
    def handle(self, *args, **options):
        with transaction.atomic():
            for obj in FirearmGoodDetails.objects.filter(
                type__in=[
                    FirearmGoodType.FIREARMS,
                    FirearmGoodType.COMPONENTS_FOR_FIREARMS,
                    FirearmGoodType.AMMUNITION,
                    FirearmGoodType.COMPONENTS_FOR_AMMUNITION,
                ]
            ):
                if obj.has_identification_markings is True:
                    obj.serial_numbers_available = FirearmGoodDetails.SN_AVAILABLE
                    obj.save()

                if obj.has_identification_markings is False:
                    obj.serial_numbers_available = FirearmGoodDetails.SN_NOT_AVAILABLE
                    obj.no_serial_numbers_reason = obj.no_identification_markings_details
                    obj.save()

