import json
import pytest

FIXTURE_BASE = "api/staticdata/report_summaries/migrations/data/0010_add_ars_prefix_dec_2024/"
INITIAL_MIGRATION = "0009_add_ars_subject_prefix_oct_2024"
MIGRATION_UNDER_TEST = "0010_add_ars_prefix_dec_2024"


@pytest.mark.django_db()
def test_add_ars_prefix_dec(migrator):
    with open(FIXTURE_BASE + "report_summary_prefix.json") as prefix_json_file:
        report_summary_prefix_data = json.load(prefix_json_file)

    old_state = migrator.apply_initial_migration(("report_summaries", INITIAL_MIGRATION))
    ReportSummaryPrefix = old_state.apps.get_model("report_summaries", "ReportSummaryPrefix")

    for prefix_to_add in report_summary_prefix_data:
        assert not ReportSummaryPrefix.objects.filter(name=prefix_to_add["name"]).exists()
        assert not ReportSummaryPrefix.objects.filter(id=prefix_to_add["id"]).exists()

    new_state = migrator.apply_tested_migration(("report_summaries", MIGRATION_UNDER_TEST))

    ReportSummaryPrefix = new_state.apps.get_model("report_summaries", "ReportSummaryPrefix")

    for expected_prefix in report_summary_prefix_data:
        prefix = ReportSummaryPrefix.objects.get(name=expected_prefix["name"])
        assert str(prefix.id) == expected_prefix["id"]
