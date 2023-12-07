from typing import Dict, Optional

from api.applications.models import GoodOnApplication
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject

from django.db.models import F, Func, Value, ExpressionWrapper, QuerySet, Subquery, OuterRef, Q, Case, When
from django.db.models.functions import Lower, StrIndex, Length
from django.db.models.fields import TextField

from django.core.management.base import BaseCommand

import csv


def annotate_normalised_summary(
    good_on_applications: QuerySet, report_summary_mappings: Optional[Dict[str, str]] = None
):
    """
    Normalise report summaries by either remapping:
        If report_summary_mappings is provided, use it to remap report_summary to a new value, if
        report_summary appears in the report_summary_mappings dictionary.

    Or normalising:
        Lower case and removing numbers in brackets and the letter x in brackets.
    """

    # Removes any numeric suffix from the report summary, also the literal string r"(x)"
    normalise_report_summary_value = Lower(
        ExpressionWrapper(
            Func(F("report_summary"), Value(r"\s\(\d+\)$|\s\(x\)$"), Value(""), function="REGEXP_REPLACE"),
            output_field=TextField(),
        ),
    )

    if not report_summary_mappings:
        normalise_report_summary = normalise_report_summary_value
    else:
        # Search for use a value from report_summary_mappings if it exists before falling back to
        # normalising the report_summary
        normalise_report_summary = Case(
            *[
                When(report_summary=original_report_summary, then=Value(new_report_summary))
                for original_report_summary, new_report_summary in report_summary_mappings.items()
            ],
            default=normalise_report_summary_value,
            output_field=TextField(),
        )
    return good_on_applications.annotate(
        normalised_report_summary=normalise_report_summary,
    )


def filter_controlled_good_on_applications(good_on_applications: QuerySet[GoodOnApplication]):
    return good_on_applications.filter(
        Q(is_good_controlled=True) | Q(is_good_controlled__isnull=True, good__is_good_controlled=True)
    )


def filter_unpopulated_controlled_good_on_applications(good_on_applications: QuerySet[GoodOnApplication]):
    return filter_controlled_good_on_applications(
        good_on_applications.filter(
            report_summary__isnull=False, report_summary_prefix__isnull=True, report_summary_subject__isnull=True
        )
    )


def annotate_matching_prefix(good_on_applications: QuerySet[GoodOnApplication]):
    # Match the longest prefix first to avoid erroneously matching a shorter query that is a subset of a longer one.
    prefixes = ReportSummaryPrefix.objects.annotate(name_length=Length("name"))

    prefix_pks = (
        prefixes.annotate(prefix_position=StrIndex(OuterRef("normalised_report_summary"), "name"))
        .filter(prefix_position=1)
        .order_by("-name_length")
        .values("pk")[:1]
    )

    return good_on_applications.annotate(suggested_prefix_id=Subquery(prefix_pks, output_field=TextField()))


class Command(BaseCommand):
    """
    Find GoodOnApplications that have a report_summary but no report_summary_prefix or report_summary_subject.

    A valid report_summary be made up of:
    - a report_summary_subject, or
    - a report_summary_prefix and a report_summary_subject seperated by a space.

    GOA with valid report_summaries will be output to the CSV passed to filename,
    GOA with invalid report_summaries will be output to stderr.
    """

    def add_arguments(self, parser):
        parser.add_argument("filename", type=str, help="Path to the output CSV file")
        parser.add_argument("--mappings", type=str, default=None, help="Path to the CSV file containing the mappings")
        parser.add_argument(
            "--review", action="store_true", help="Output columns to aid human review (good_name, uat_link)"
        )
        parser.add_argument(
            "--review-env", type=str, default="uat", help="Review environment to use (uat, staging, production)"
        )

    @staticmethod
    def _get_suggested_subject(normalised_report_summary: str, suggested_prefix: ReportSummaryPrefix):
        if suggested_prefix:
            return normalised_report_summary.rsplit(f"{suggested_prefix.name} ", maxsplit=1)[1]
        return normalised_report_summary

    def handle(self, *args, **options):
        mappings_file = options["mappings"]
        filename = options["filename"]
        is_for_review = options["review"]

        url_format = (
            "https://internal.lite.service."
            + options["review_env"]
            + ".uktrade.digital/queues/00000000-0000-0000-0000-000000000001/cases/{case_id}"
            + "/tau/edit/{good_on_application_id}"
        )
        report_summary_mappings: Dict[str, str] = {}
        if mappings_file:
            with open(mappings_file, "r") as f:
                csv_headers = ["original_report_summary", "corrected_report_summary"]
                reader = csv.DictReader(f, fieldnames=csv_headers, skipinitialspace=True)
                next(reader)
                for row in reader:
                    report_summary_mappings[row["original_report_summary"]] = row["corrected_report_summary"]

        good_on_applications = filter_unpopulated_controlled_good_on_applications(
            GoodOnApplication.objects.order_by("report_summary")
        )
        good_on_applications = annotate_normalised_summary(good_on_applications, report_summary_mappings)
        good_on_applications = annotate_matching_prefix(good_on_applications)

        csv_headers = (
            "id",
            "report_summary",
            "suggested_prefix",
            "suggested_prefix_id",
            "suggested_subject",
            "suggested_subject_id",
            *(["good_name", "url"] if is_for_review else []),
        )
        prefixes_by_id = {
            report_summary_prefix.id: report_summary_prefix
            for report_summary_prefix in ReportSummaryPrefix.objects.all()
        }
        subjects_by_name = {
            report_summary_subject.name: report_summary_subject
            for report_summary_subject in ReportSummarySubject.objects.all()
        }

        with open(filename, "w") as csvfile:
            has_written_unmappables_csv_header = False
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers, quoting=csv.QUOTE_ALL)
            writer.writeheader()

            stderr_writer = csv.DictWriter(self.stderr, fieldnames=csv_headers, quoting=csv.QUOTE_ALL)
            for good_on_application in good_on_applications:
                suggested_prefix = prefixes_by_id.get(good_on_application.suggested_prefix_id)

                suggested_subject_name = self._get_suggested_subject(
                    good_on_application.normalised_report_summary, suggested_prefix
                )
                suggested_subject = subjects_by_name.get(suggested_subject_name)

                data = {
                    "id": good_on_application.id,
                    "report_summary": good_on_application.report_summary,
                    "suggested_prefix": suggested_prefix.name if suggested_prefix else "",
                    "suggested_prefix_id": good_on_application.suggested_prefix_id
                    if good_on_application.suggested_prefix_id
                    else "",
                    "suggested_subject": suggested_subject.name if suggested_subject else "",
                    "suggested_subject_id": suggested_subject.id if suggested_subject else "",
                    **(
                        {
                            "good_name": good_on_application.good.name,
                            "url": url_format.format(
                                case_id=good_on_application.application.id,
                                good_on_application_id=good_on_application.id,
                            ),
                        }
                        if is_for_review
                        else {}
                    ),
                }

                if suggested_subject:
                    # Valid GOA have a suggested subject and are written to the CSV file.
                    writer.writerow(data)
                else:
                    # Invalid GOA do not have a suggested subject and are written to stderr.
                    # If this is the first GOA with no suggested subject, write the header
                    if not has_written_unmappables_csv_header:  # pragma: nocover  - nocov validated by @currycoder
                        has_written_unmappables_csv_header = True
                        stderr_writer.writeheader()

                    stderr_writer.writerow(data)
