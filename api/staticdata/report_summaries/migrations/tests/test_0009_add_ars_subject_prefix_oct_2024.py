import json
import pytest

FIXTURE_BASE = "api/staticdata/report_summaries/migrations/data/0009_add_report_summaries_oct_2024/"
INITIAL_MIGRATION = "0008_back_populate_multiple_ars_data"
MIGRATION_UNDER_TEST = "0009_add_ars_subject_prefix_oct_2024"


@pytest.mark.django_db()
def test_add_cles(migrator):
    with open(FIXTURE_BASE + "report_summary_prefix.json") as prefix_json_file:
        report_summary_prefix_data = json.load(prefix_json_file)

    with open(FIXTURE_BASE + "report_summary_subject.json") as subject_json_file:
        report_summary_subject_data = json.load(subject_json_file)

    old_state = migrator.apply_initial_migration(("report_summaries", INITIAL_MIGRATION))
    ReportSummaryPrefix = old_state.apps.get_model("report_summaries", "ReportSummaryPrefix")
    ReportSummarySubject = old_state.apps.get_model("report_summaries", "ReportSummarySubject")

    for prefix_to_add in report_summary_prefix_data:
        assert not ReportSummaryPrefix.objects.filter(name=prefix_to_add["name"]).exists()

    for subject_to_add in report_summary_subject_data:
        assert not ReportSummarySubject.objects.filter(name=subject_to_add["name"]).exists()

    new_state = migrator.apply_tested_migration(("report_summaries", MIGRATION_UNDER_TEST))

    ReportSummaryPrefix = new_state.apps.get_model("report_summaries", "ReportSummaryPrefix")
    ReportSummarySubject = new_state.apps.get_model("report_summaries", "ReportSummarySubject")

    for expected_prefix in report_summary_prefix_data:
        prefix = ReportSummaryPrefix.objects.get(name=expected_prefix["name"])
        assert str(prefix.id) == expected_prefix["id"]

    for expected_subject in report_summary_subject_data:
        subject = ReportSummarySubject.objects.get(name=expected_subject["name"])
        assert str(subject.id) == expected_subject["id"]
        assert subject.code_level == expected_subject["code_level"]
