from moto import mock_aws

from pytest_bdd import (
    given,
    parsers,
    scenarios,
    then,
    when,
)

from django.conf import settings
from django.urls import reverse

from api.applications.enums import ApplicationExportType
from api.applications.tests.factories import DraftStandardApplicationFactory
from api.documents.libraries.s3_operations import init_s3_client
from api.parties.tests.factories import PartyDocumentFactory


scenarios("./scenarios/applications.feature")


@given("a draft standard application", target_fixture="draft_standard_application")
def given_draft_standard_application(organisation):
    application = DraftStandardApplicationFactory(
        organisation=organisation,
    )

    PartyDocumentFactory(
        party=application.end_user.party,
        s3_key="party-document",
        safe=True,
    )

    return application


def parse_attributes(attributes):
    kwargs = {}
    for attribute in attributes.split("\n"):
        if not attribute:
            continue
        key, _, value = attribute.partition(":")
        kwargs[key.strip()] = value.strip()
    return kwargs


@given(
    parsers.parse("a draft standard application with attributes:{attributes}"),
    target_fixture="draft_standard_application",
)
def given_a_draft_standard_application_with_attributes(organisation, attributes):
    application = DraftStandardApplicationFactory(
        organisation=organisation,
        **parse_attributes(attributes),
    )

    PartyDocumentFactory(
        party=application.end_user.party,
        s3_key="party-document",
        safe=True,
    )

    return application


@given(
    parsers.parse("a draft temporary standard application with attributes:{attributes}"),
    target_fixture="draft_standard_application",
)
def given_a_draft_standard_application_with_attributes(organisation, attributes):
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


@when("the application is submitted")
def when_the_application_is_submitted(api_client, exporter_headers, draft_standard_application, mocker):
    type_code = "T" if draft_standard_application.export_type == ApplicationExportType.TEMPORARY else "P"
    reference_code = f"GBSIEL/2024/0000001/{type_code}"
    mocker.patch("api.cases.models.generate_reference_code", return_value=reference_code)
    with mock_aws():
        s3 = init_s3_client()
        s3.create_bucket(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            CreateBucketConfiguration={
                "LocationConstraint": settings.AWS_REGION,
            },
        )
        response = api_client.put(
            reverse(
                "applications:application_submit",
                kwargs={
                    "pk": draft_standard_application.pk,
                },
            ),
            data={
                "submit_declaration": True,
                "agreed_to_declaration_text": "i agree",
            },
            **exporter_headers,
        )
        assert response.status_code == 200, response.json()["errors"]


@then(parsers.parse("the application status is set to {status}"))
def then_the_application_status_is_set_to(draft_standard_application, status):
    draft_standard_application.refresh_from_db()
    assert (
        draft_standard_application.status.status == status
    ), f"Application status is not {status} it is {draft_standard_application.status.status}"
