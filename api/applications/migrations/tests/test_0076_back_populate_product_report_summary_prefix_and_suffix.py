import csv
from unittest.mock import patch

import pytest
from django.db.migrations.state import ProjectState


@pytest.fixture(scope="function")
def tmp_migrations_csv_path(tmp_path_factory, settings):
    """Create directory for migrations CSV files and configure settings to use it."""
    migrations_data_path = tmp_path_factory.mktemp("migrations")
    return migrations_data_path


@pytest.fixture(scope="function")
def tmp_application_migrations_csv_dir(tmp_migrations_csv_path):
    applications_migrations_csv_dir = tmp_migrations_csv_path / "applications"
    applications_migrations_csv_dir.mkdir(parents=True)
    return applications_migrations_csv_dir


def good_on_application_factory(project_state: ProjectState, **kwargs):
    CaseStatus = project_state.apps.get_model("statuses", "CaseStatus")  # noqa N806
    Good = project_state.apps.get_model("goods", "Good")  # noqa N806
    GoodOnApplication = project_state.apps.get_model("applications", "GoodOnApplication")  # noqa N806
    StandardApplication = project_state.apps.get_model("applications", "StandardApplication")  # noqa N806
    Organisation = project_state.apps.get_model("organisations", "Organisation")  # noqa N806
    Case = project_state.apps.get_model("cases", "Case")  # noqa N806
    CaseType = project_state.apps.get_model("cases", "CaseType")  # noqa N806

    case_status = CaseStatus.objects.get(status="submitted")
    case_type = CaseType.objects.get(type="application", reference="oiel", sub_type="open")

    organisation = Organisation.objects.create(name="test")
    case = Case.objects.create(case_type=case_type, organisation=organisation)
    application = StandardApplication.objects.create(
        organisation=organisation, case_type=case_type, case=case, status=case_status
    )
    good = Good.objects.create(name="test", organisation=organisation)
    good_on_application = GoodOnApplication.objects.create(application=application, good=good, **kwargs)

    return good_on_application


@pytest.mark.django_db()
def test_report_summary_prefix_suffix_population_from_csv(
    migrator, tmp_migrations_csv_path, tmp_application_migrations_csv_dir
):
    # Test that the data migration correctly maps data from the input CSV.
    # Note on the data: Prefixes are chosen where the name of one is a substring of the other to help verify the prefix
    # mapping works correctly.
    data = [
        # report_summary, expected_prefix, expected_subject
        ("dogs", None, "dogs"),
        ("technology for dogs", "technology_for", "dogs"),
        (
            "technology for production installations for dinosaurs",
            "technology for production installations for dinosaurs",
            "dinosaurs",
        ),
        (
            "technology for production installations for dogs",
            "technology for production installations for dogs",
            "dogs",
        ),
    ]
    report_summary_data, prefix_data, subject_data = zip(*data)

    old_state = migrator.apply_initial_migration(
        ("applications", "0075_back_populate_product_report_summary_prefix_and_suffix")
    )

    OldReportSummaryPrefix = old_state.apps.get_model("report_summaries", "ReportSummaryPrefix")  # noqa N806
    OldReportSummarySubject = old_state.apps.get_model("report_summaries", "ReportSummarySubject")  # noqa N806

    old_report_prefixes = {
        report_summary: OldReportSummaryPrefix.objects.get_or_create(name=prefix_name)[0] if prefix_name else None
        for report_summary, prefix_name, _ in data
    }

    old_report_subjects = {
        report_summary: OldReportSummarySubject.objects.get_or_create(name=subject_name, code_level=1)[0]
        for report_summary, _, subject_name in data
    }

    old_good_on_applications = [
        good_on_application_factory(old_state, report_summary=report_summary) for report_summary in report_summary_data
    ]

    old_good_on_application__pks = {old_good_on_application.pk for old_good_on_application in old_good_on_applications}

    with open(
        str(tmp_application_migrations_csv_dir / "0076_back_populate_product_report_summary_prefix_and_suffix.csv"),
        "w",
        newline="",
    ) as csvfile:
        csv_writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        csv_writer.writerow(
            [
                "id",
                "report_summary",
                "suggested_prefix",
                "suggested_prefix_id",
                "suggested_subject",
                "suggested_subject_id",
            ]
        )
        for good_on_application in old_good_on_applications:
            assert good_on_application.report_summary is not None
            prefix = old_report_prefixes[good_on_application.report_summary]
            subject = old_report_subjects[good_on_application.report_summary]
            assert subject is not None
            csv_writer.writerow(
                [
                    str(good_on_application.id),
                    good_on_application.report_summary,
                    prefix.name if prefix else None,
                    str(prefix.id) if prefix else None,
                    subject.name,
                    subject.id,
                ]
            )

    with patch(
        "api.applications.migrations.0076_back_populate_product_report_summary_prefix_and_suffix.Migration.get_csv_path",
        side_effect=[
            tmp_application_migrations_csv_dir / "0076_back_populate_product_report_summary_prefix_and_suffix.csv"
        ],
    ) as mock_get_csv_path:
        new_state = migrator.apply_tested_migration(
            ("applications", "0076_back_populate_product_report_summary_prefix_and_suffix")
        )

        mock_get_csv_path.assert_called_once()

    GoodOnApplication = new_state.apps.get_model("applications", "GoodOnApplication")  # noqa N806
    ReportSummaryPrefix = new_state.apps.get_model("report_summaries", "ReportSummaryPrefix")  # noqa N806
    ReportSummarySubject = new_state.apps.get_model("report_summaries", "ReportSummarySubject")  # noqa N806

    new_good_on_applications = GoodOnApplication.objects.filter(pk__in=old_good_on_application__pks)
    assert set(new_good_on_applications.values_list("pk", flat=True)) == old_good_on_application__pks

    for new_good_on_application in new_good_on_applications:
        assert (
            new_good_on_application.report_summary_subject.id
            == old_report_subjects[new_good_on_application.report_summary].id
        )
        assert (
            new_good_on_application.report_summary_subject.name
            == old_report_subjects[new_good_on_application.report_summary].name
        )
        if new_good_on_application.report_summary_prefix is None:
            assert new_good_on_application.report_summary_prefix is None
        else:
            assert (
                new_good_on_application.report_summary_prefix.id
                == old_report_prefixes[new_good_on_application.report_summary].id
            )
            assert (
                new_good_on_application.report_summary_prefix.name
                == old_report_prefixes[new_good_on_application.report_summary].name
            )
