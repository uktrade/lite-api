from api.applications.models import GoodOnApplication
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject

from django.db.models import F, Func, Value, ExpressionWrapper, QuerySet, Subquery, OuterRef, Q
from django.db.models.functions import Lower, StrIndex, Length
from django.db.models.fields import TextField

from django.core.management.base import BaseCommand

import csv


def annotate_normalised_summary(good_on_applications: QuerySet):
    return good_on_applications.annotate(
        # Remove any numeric suffix from the report summary, also the literal string r"(x)"
        normalised_report_summary=Lower(
            ExpressionWrapper(
                Func(F("report_summary"), Value(r"\s\(\d+\)$|\s\(x\)$"), Value(""), function="REGEXP_REPLACE"),
                output_field=TextField(),
            ),
        ),
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


def filter_populated_controlled_good_on_applications(good_on_applications: QuerySet[GoodOnApplication]):
    return filter_controlled_good_on_applications(good_on_applications).filter(report_summary_subject__isnull=False)


def annotate_matching_prefix(good_on_applications: QuerySet[GoodOnApplication]):
    # Match the longest prefix first to avoid erroneously matching a shorter query that is a subset of a longer one.
    prefixes = ReportSummaryPrefix.objects.annotate(name_length=Length("name"))

    prefix_pks = (
        prefixes.annotate(prefix_position=StrIndex(OuterRef("report_summary"), "name"))
        .filter(prefix_position=1)
        .order_by("-name_length")
        .values("pk")[:1]
    )

    return good_on_applications.annotate(suggested_prefix_id=Subquery(prefix_pks, output_field=TextField()))


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("filename", type=str, help="Path to the output CSV file")

    @staticmethod
    def _get_suggested_subject(normalised_report_summary: str, suggested_prefix: ReportSummaryPrefix):
        if suggested_prefix:
            return normalised_report_summary.rsplit(f"{suggested_prefix.name} ", maxsplit=1)[1]
        return normalised_report_summary

    def handle(self, *args, **options):
        filename = options["filename"]

        good_on_applications = filter_unpopulated_controlled_good_on_applications(
            GoodOnApplication.objects.order_by("report_summary")
        )
        good_on_applications = annotate_normalised_summary(good_on_applications)
        good_on_applications = annotate_matching_prefix(good_on_applications)

        csv_headers = (
            "id",
            "report_summary",
            "suggested_prefix",
            "suggested_prefix_id",
            "suggested_subject",
            "suggested_subject_id",
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
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for good_on_application in good_on_applications:
                suggested_prefix = prefixes_by_id.get(good_on_application.suggested_prefix_id)

                suggested_subject_name = self._get_suggested_subject(
                    good_on_application.normalised_report_summary, suggested_prefix
                )
                suggested_subject = subjects_by_name.get(suggested_subject_name)
                if suggested_subject is None:
                    self.stderr.write(
                        f"{good_on_application.id}, {good_on_application.normalised_report_summary}  "
                        "[SKIPPED: No suggested subject]"
                    )
                    continue

                data = {
                    "id": good_on_application.id,
                    "report_summary": good_on_application.report_summary,
                    "suggested_prefix": suggested_prefix.name if suggested_prefix else "",
                    "suggested_prefix_id": good_on_application.suggested_prefix_id
                    if good_on_application.suggested_prefix_id
                    else "",
                    "suggested_subject": suggested_subject.name,
                    "suggested_subject_id": suggested_subject.id,
                }
                writer.writerow(data)

        self.stderr.write(f"Saved: {filename}")
