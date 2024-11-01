import logging
from django.core.management.base import BaseCommand, CommandError

from api.cases.models import Case
from api.organisations.models import Organisation, Site
from api.support.helpers import developer_intervention

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
        Command to change the primary site of an organisation to another site.

        An exporter may need to change the site used for an application while
        a case is in progress. A new site can be created by the exporter but it
        cannot be set as the primary site through the UI. This command is a way
        to change the primary site to another site that the exporter already
        has linked to their organisation.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--case_reference", type=str, nargs="?", help="Reference code of the Case (e.g. GBSIEL/2024/0000001/P)."
        )
        parser.add_argument(
            "--organisation_id", type=str, nargs="?", help="The primary key 'id' of the Organisation to be updated."
        )
        parser.add_argument(
            "--site_id_to_set",
            type=str,
            nargs="?",
            help="The primary key 'id' of the Site to be set as the primary site.",
        )
        parser.add_argument("--dry_run", help="Is it a test run?", action="store_true")

    def handle(self, *args, **options):
        case_reference = options.pop("case_reference")
        organisation_id = options.pop("organisation_id")
        site_id_to_set = options.pop("site_id_to_set")
        dry_run = options.pop("dry_run")

        with developer_intervention(dry_run=dry_run) as audit_log:
            try:
                case = Case.objects.get(reference_code=case_reference)
            except Case.DoesNotExist as e:
                logger.error("Invalid Case reference %s, does not exist", case_reference)
                raise CommandError(e)

            try:
                organisation = Organisation.objects.get(id=organisation_id)
            except Organisation.DoesNotExist as e:
                logger.error("Invalid Organisation id %s, does not exist", organisation_id)
                raise CommandError(e)

            try:
                site_to_set = Site.objects.get(id=site_id_to_set)
            except Site.DoesNotExist as e:
                logger.error("Invalid Site id %s, does not exist", site_id_to_set)
                raise CommandError(e)

            # Ensure that the site to set belongs to the organisation
            if not site_to_set in organisation.site.all():
                logger.error("Invalid Site to set, Site not linked to Organisation")
                raise CommandError(Exception("Invalid Site to set, Site not linked to Organisation"))

            organisation.primary_site = site_to_set
            organisation.save()

            audit_log(case, "Changed primary site.")

            logging.info("[%s] can now be progressed with the new primary site", case_reference)
