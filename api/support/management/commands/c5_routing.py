import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from lite_routing.routing_rules_internal.tests.helpers import activate_c5_routing, deactivate_c5_routing


class Command(BaseCommand):
    help = """
    Command to activate/deactivate preset flagging and routing rules for C5

    To test	C5 routing we will need	to activate few	flagging/routing rules and
    deactivate some	of the existing	ones. We need to do this multiple times
    as we add more rules.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "state", type=str, help="State to be set for flagging and routing rules (activate|deactivate)"
        )

    def handle(self, *args, **options):
        state = options.pop("state")

        with transaction.atomic():
            if state == "activate":
                logging.info("Activating C5 related routing and flagging rules")
                activate_c5_routing()

            if state == "deactivate":
                logging.info("Deactivating C5 related routing and flagging rules")
                deactivate_c5_routing()
