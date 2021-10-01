import logging

from django.core.management.base import BaseCommand

from api.cases.models import Case


class Command(BaseCommand):
    help = """
        Command to mark unresolved ECJU queries as resolved.

        Usually if Exporter replies to an ECJU query then that query is marked as resolved.
        In some cases some duplicate queries are observed with the same timestamp, at this point
        it is not certain whether they are created intentionally or because of a bug so further
        investigation is required.

        But if any case has unresolved queries it won't be visible to caseworkers and delay the process
        hence this command is being added to mark them as resolved to allow the case to progress.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "case_reference", type=str, help="Reference number of the application",
        )
        parser.add_argument(
            "--dry_run", action="store_true", help="Print out what action will happen without applying any changes"
        )

    def handle(self, *args, **options):
        case_reference = options.pop("case_reference")
        dry_run = options["dry_run"]
        logging.info(f"Given case reference is: {case_reference}")

        try:
            case = Case.objects.get(reference_code=case_reference)
        except Case.DoesNotExist:
            logging.error(f"Case ({case_reference}) not found, please provide valid case reference")
            return

        unresolved_queries = case.case_ecju_query.filter(response=None)
        if unresolved_queries.count() == 0:
            logging.info(f"No unresolved queries for Case {case_reference} found, returning.")
            return

        logging.info(f"Number of unresolved queries for Case {case_reference}: {unresolved_queries.count()}")

        for query in unresolved_queries:
            query.response = "Marked as resolved by LITE System"
            if not dry_run:
                query.save()

        logging.info(
            f"Number of unresolved queries after update for Case {case_reference}: {case.case_ecju_query.filter(response=None).count()}"
        )
