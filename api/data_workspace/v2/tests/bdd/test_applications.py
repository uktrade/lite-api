import pytest
from django.urls import reverse
from freezegun import freeze_time
from pytest_bdd import given, parsers, scenarios, when

from api.applications.enums import ApplicationExportType
from api.applications.tests.factories import (
    DraftStandardApplicationFactory,
    GoodOnApplicationFactory,
    PartyOnApplicationFactory,
)
from api.data_workspace.v2.tests.bdd.conftest import run_processing_time_task
from api.parties.tests.factories import PartyDocumentFactory, UltimateEndUserFactory
from api.staticdata.statuses.enums import CaseStatusEnum

scenarios("./scenarios/applications.feature")


@pytest.fixture
def submit_application(api_client, exporter_headers, mocker):
    def _submit_application(draft_application):
        type_code = "T" if draft_application.export_type == ApplicationExportType.TEMPORARY else "P"
        reference_code = f"GBSIEL/2024/0000001/{type_code}"
        mocker.patch("api.cases.models.generate_reference_code", return_value=reference_code)

        response = api_client.put(
            reverse(
                "applications:application_submit",
                kwargs={
                    "pk": draft_application.pk,
                },
            ),
            data={
                "submit_declaration": True,
                "agreed_to_declaration_text": "i agree",
            },
            **exporter_headers,
        )
        assert response.status_code == 200, response.json()["errors"]

        draft_application.refresh_from_db()
        return draft_application

    return _submit_application


@pytest.fixture()
def exporter_change_status(api_client, exporter_headers):
    def _exporter_change_status(application, status):
        response = api_client.post(
            reverse(
                "exporter_applications:change_status",
                kwargs={
                    "pk": application.pk,
                },
            ),
            data={
                "status": status,
            },
            **exporter_headers,
        )
        assert response.status_code == 200, response.content

    return _exporter_change_status


@given(
    parsers.parse("a draft temporary standard application with attributes:{attributes}"),
    target_fixture="draft_standard_application",
)
def given_a_draft_temporary_standard_application_with_attributes(organisation, parse_attributes, attributes):
    application = DraftStandardApplicationFactory(
        export_type=ApplicationExportType.TEMPORARY,
        temp_export_details="temporary export details",
        is_temp_direct_control=True,
        proposed_return_date="2025-05-11",
        organisation=organisation,
        **parse_attributes(attributes),
    )

    PartyDocumentFactory(
        party=application.end_user.party,
        s3_key="party-document",
        safe=True,
    )

    return application


@given("a good where the exporter said yes to the product being incorporated into another product")
def given_a_good_is_good_incorporated(draft_standard_application):
    PartyOnApplicationFactory(
        application=draft_standard_application,
        party=UltimateEndUserFactory(organisation=draft_standard_application.organisation),
    )
    GoodOnApplicationFactory(
        application=draft_standard_application,
        is_good_incorporated=True,
    )


@given("a good where the exporter said yes to the product being incorporated before it is onward exported")
def given_a_good_is_onward_incorporated(draft_standard_application):
    PartyOnApplicationFactory(
        application=draft_standard_application,
        party=UltimateEndUserFactory(organisation=draft_standard_application.organisation),
    )
    GoodOnApplicationFactory(
        application=draft_standard_application,
        is_onward_incorporated=True,
    )


@when(
    parsers.parse("the application is submitted at {submission_time}"),
    target_fixture="submitted_standard_application",
)
def when_the_application_is_submitted_at(submit_application, draft_standard_application, submission_time):
    with freeze_time(submission_time):
        return submit_application(draft_standard_application)


@when(parsers.parse("the application is withdrawn at {timestamp}"))
def when_the_application_is_withdrawn_at(
    submitted_standard_application,
    exporter_change_status,
    timestamp,
):
    run_processing_time_task(submitted_standard_application.submitted_at, timestamp)

    with freeze_time(timestamp):
        exporter_change_status(submitted_standard_application, CaseStatusEnum.WITHDRAWN)

    submitted_standard_application.refresh_from_db()


@when(parsers.parse("the application is surrendered at {timestamp}"))
def when_the_application_is_surrendered_at(
    submitted_standard_application,
    exporter_change_status,
    timestamp,
):
    run_processing_time_task(submitted_standard_application.submitted_at, timestamp)

    with freeze_time(timestamp):
        exporter_change_status(submitted_standard_application, CaseStatusEnum.SURRENDERED)

    submitted_standard_application.refresh_from_db()


@when(parsers.parse("the application is closed at {timestamp}"))
def when_the_application_is_closed_at(
    submitted_standard_application,
    caseworker_change_status,
    timestamp,
):
    run_processing_time_task(submitted_standard_application.submitted_at, timestamp)

    with freeze_time(timestamp):
        caseworker_change_status(submitted_standard_application, CaseStatusEnum.CLOSED)

    submitted_standard_application.refresh_from_db()
