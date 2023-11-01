from api.applications.models import GoodOnApplication
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject

from django.db.models import F, Func, Value, ExpressionWrapper, Subquery, OuterRef, Q
from django.db.models.functions import Lower, StrIndex, Length
from django.db.models.fields import IntegerField, TextField

from django.core.management.base import BaseCommand

import csv


def annotate_normalised_summary(q):
    return q.annotate(
        # Remove any numeric suffix from the report summary, also the literal string r"(x)"
        normalised_report_summary=Lower(
            ExpressionWrapper(
                Func(F("report_summary"), Value(r"\s\(\d+\)$|\s\(x\)$"), Value(""), function="REGEXP_REPLACE"),
                output_field=TextField(),
            ),
        ),
    )


def filter_controlled_good_on_applications(q):
    return q.filter(Q(Q(is_good_controlled=True) | Q(is_good_controlled__isnull=True, good__is_good_controlled=True)))


def filter_unpopulated_controlled_good_on_applications(q):
    return filter_controlled_good_on_applications(
        q.filter(report_summary__isnull=False, report_summary_prefix__isnull=True, report_summary_subject__isnull=True)
    )


def filter_populated_controlled_good_on_applications(q):
    return filter_controlled_good_on_applications(q).filter(report_summary_subject__isnull=False)


def annotate_matching_prefix(q):
    # Match the longest prefix first.
    prefixes = ReportSummaryPrefix.objects.annotate(name_length=Length("name"))

    best_matching_prefix = (
        prefixes.annotate(prefix_position=StrIndex(OuterRef("report_summary"), "name"))
        .filter(prefix_position=1)
        .order_by("-name_length")
        .values("pk")[:1]
    )

    q = q.annotate(suggested_prefix_id=Subquery(best_matching_prefix, output_field=TextField()))
    return q


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("filename", type=str, help="Path to the input CSV file")

    def _get_suggested_subject(self, normalised_report_summary: str, suggested_prefix: ReportSummaryPrefix):
        if suggested_prefix:
            return normalised_report_summary.rsplit(f"{suggested_prefix.name} ", maxsplit=1)[1]
        return normalised_report_summary

    def handle(self, *args, **options):
        filename = options["filename"]

        q = filter_unpopulated_controlled_good_on_applications(GoodOnApplication.objects.order_by("report_summary"))

        q = annotate_normalised_summary(q)
        q = annotate_matching_prefix(q)

        csv_headers = (
            "id",
            "report_summary",
            "suggested_prefix",
            "suggested_prefix_id",
            "suggested_subject",
            "suggested_subject_id",
        )
        prefixes_by_id = {o.id: o for o in ReportSummaryPrefix.objects.all()}
        subjects_by_name = {o.name: o for o in ReportSummarySubject.objects.all()}

        with open(filename, "w") as infile:
            writer = csv.DictWriter(infile, fieldnames=csv_headers, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for o in q:
                suggested_prefix = prefixes_by_id.get(o.suggested_prefix_id)

                suggested_subject_name = self._get_suggested_subject(o.normalised_report_summary, suggested_prefix)
                suggested_subject = subjects_by_name.get(suggested_subject_name)
                if suggested_subject is None:
                    self.stderr.write(f"{o.id}, {o.normalised_report_summary}  [SKIPPED: No suggested subject]")
                    continue

                data = {
                    "id": o.id,
                    "report_summary": o.report_summary,
                    "suggested_prefix": suggested_prefix.name if suggested_prefix else "",
                    "suggested_prefix_id": o.suggested_prefix_id if o.suggested_prefix_id else "",
                    "suggested_subject": suggested_subject.name,
                    "suggested_subject_id": suggested_subject.id,
                }
                writer.writerow(data)

        self.stderr.write(f"Saved: {filename}")
