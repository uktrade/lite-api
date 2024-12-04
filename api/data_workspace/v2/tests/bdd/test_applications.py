import pytest

from freezegun import freeze_time

from pytest_bdd import (
    given,
    parsers,
    scenarios,
    when,
)

from django.urls import reverse

from api.applications.enums import ApplicationExportType
from api.applications.tests.factories import (
    DraftStandardApplicationFactory,
    GoodOnApplicationFactory,
    PartyOnApplicationFactory,
)
from api.cases.enums import (
    AdviceLevel,
    AdviceType,
)
from api.licences.enums import LicenceStatus
from api.parties.tests.factories import (
    PartyDocumentFactory,
    UltimateEndUserFactory,
)
from api.staticdata.statuses.enums import CaseStatusEnum
from api.data_workspace.v2.tests.bdd.conftest import run_processing_time_task

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
def caseworker_change_status(api_client, lu_case_officer, lu_case_officer_headers):
    def _caseworker_change_status(application, status):
        url = reverse(
            "caseworker_applications:change_status",
            kwargs={
                "pk": str(application.pk),
            },
        )
        response = api_client.post(
            url,
            data={"status": status},
            **lu_case_officer_headers,
        )
        assert response.status_code == 200, response.content
        application.refresh_from_db()
        assert application.status.status == status

    return _caseworker_change_status


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


@when(parsers.parse("the application is refused at {timestamp}"), target_fixture="refused_application")
def when_the_application_is_refused_at(
    submitted_standard_application,
    refuse_application,
    timestamp,
):
    run_processing_time_task(submitted_standard_application.submitted_at, timestamp)

    with freeze_time(timestamp):
        refuse_application(submitted_standard_application)

    submitted_standard_application.refresh_from_db()
    refused_application = submitted_standard_application

    return refused_application


@when(parsers.parse("the application is appealed at {timestamp}"), target_fixture="appealed_application")
def when_the_application_is_appealed_at(
    refused_application,
    api_client,
    exporter_headers,
    timestamp,
):
    with freeze_time(timestamp):
        response = api_client.post(
            reverse(
                "applications:appeals",
                kwargs={
                    "pk": refused_application.pk,
                },
            ),
            data={
                "grounds_for_appeal": "This is appealing",
            },
            **exporter_headers,
        )
        assert response.status_code == 201, response.content

    refused_application.refresh_from_db()
    appealed_application = refused_application

    return appealed_application


@when(parsers.parse("the refused application is issued on appeal at {timestamp}"))
def when_the_application_is_issued_on_appeal_at(
    appealed_application,
    timestamp,
    caseworker_change_status,
    issue_licence,
):
    run_processing_time_task(appealed_application.appeal.created_at, timestamp)

    with freeze_time(timestamp):
        appealed_application.advice.filter(level=AdviceLevel.FINAL).update(
            type=AdviceType.APPROVE,
            text="issued on appeal",
        )

        caseworker_change_status(appealed_application, CaseStatusEnum.REOPENED_FOR_CHANGES)
        caseworker_change_status(appealed_application, CaseStatusEnum.UNDER_FINAL_REVIEW)
        issue_licence(appealed_application)


@when(parsers.parse("the issued application is revoked at {timestamp}"))
def when_the_issued_application_is_revoked(
    api_client,
    lu_sr_manager_headers,
    issued_application,
    timestamp,
):
    run_processing_time_task(issued_application.submitted_at, timestamp)

    with freeze_time(timestamp):
        issued_licence = issued_application.licences.get()
        url = reverse("licences:licence_details", kwargs={"pk": str(issued_licence.pk)})
        response = api_client.patch(
            url,
            data={"status": LicenceStatus.REVOKED},
            **lu_sr_manager_headers,
        )
        assert response.status_code == 200, response.status_code


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
