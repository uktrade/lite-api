import datetime
from freezegun import freeze_time

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
from api.applications.tests.factories import (
    DraftStandardApplicationFactory,
    GoodOnApplicationFactory,
    PartyOnApplicationFactory,
)
from api.cases.enums import (
    AdviceLevel,
    AdviceType,
)
from api.cases.tests.factories import FinalAdviceFactory
from api.documents.libraries.s3_operations import init_s3_client
from api.flags.enums import SystemFlags
from api.licences.enums import LicenceStatus
from api.parties.tests.factories import (
    PartyDocumentFactory,
    UltimateEndUserFactory,
)
from api.staticdata.statuses.enums import CaseStatusEnum


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


@when("the application is submitted", target_fixture="submitted_standard_application")
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
    draft_standard_application.refresh_from_db()
    return draft_standard_application


@when(parsers.parse("the application is issued at {timestamp}"), target_fixture="issued_application")
def when_the_application_is_issued_at(
    api_client, lu_case_officer, siel_template, gov_headers, submitted_standard_application, timestamp
):
    with freeze_time(timestamp):
        data = {"action": AdviceType.APPROVE, "duration": 24}
        for good_on_app in submitted_standard_application.goods.all():
            good_on_app.quantity = 100
            good_on_app.value = 10000
            good_on_app.save()
            data[f"quantity-{good_on_app.id}"] = str(good_on_app.quantity)
            data[f"value-{good_on_app.id}"] = str(good_on_app.value)
            FinalAdviceFactory(user=lu_case_officer, case=submitted_standard_application, good=good_on_app.good)

        issue_date = datetime.datetime.fromisoformat(timestamp)
        data.update({"year": issue_date.year, "month": issue_date.month, "day": issue_date.day})

        submitted_standard_application.flags.remove(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

        url = reverse("applications:finalise", kwargs={"pk": submitted_standard_application.pk})
        response = api_client.put(url, data=data, **gov_headers)
        assert response.status_code == 200, response.content
        response = response.json()

        with mock_aws():
            s3 = init_s3_client()
            s3.create_bucket(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                CreateBucketConfiguration={
                    "LocationConstraint": settings.AWS_REGION,
                },
            )
            data = {
                "template": str(siel_template.id),
                "text": "",
                "visible_to_exporter": False,
                "advice_type": AdviceType.APPROVE,
            }
            url = reverse(
                "cases:generated_documents:generated_documents",
                kwargs={"pk": str(submitted_standard_application.pk)},
            )
            response = api_client.post(url, data=data, **gov_headers)
            assert response.status_code == 201, response.content

        url = reverse(
            "cases:finalise",
            kwargs={"pk": str(submitted_standard_application.pk)},
        )
        response = api_client.put(url, data={}, **gov_headers)
        assert response.status_code == 201

        return submitted_standard_application


@when(parsers.parse("the application is refused at {timestamp}"), target_fixture="refused_application")
def when_the_application_is_refused_at(
    api_client, lu_case_officer, siel_refusal_template, gov_headers, submitted_standard_application, timestamp
):
    with freeze_time(timestamp):
        data = {"action": AdviceType.REFUSE}
        for good_on_app in submitted_standard_application.goods.all():
            good_on_app.quantity = 100
            good_on_app.value = 10000
            good_on_app.save()
            data[f"quantity-{good_on_app.id}"] = str(good_on_app.quantity)
            data[f"value-{good_on_app.id}"] = str(good_on_app.value)
            FinalAdviceFactory(
                user=lu_case_officer,
                case=submitted_standard_application,
                good=good_on_app.good,
                type=AdviceType.REFUSE,
            )

        submitted_standard_application.flags.remove(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

        url = reverse("applications:finalise", kwargs={"pk": submitted_standard_application.pk})
        response = api_client.put(url, data=data, **gov_headers)
        assert response.status_code == 200, response.content
        response = response.json()

        with mock_aws():
            s3 = init_s3_client()
            s3.create_bucket(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                CreateBucketConfiguration={
                    "LocationConstraint": settings.AWS_REGION,
                },
            )
            data = {
                "template": str(siel_refusal_template.id),
                "text": "",
                "visible_to_exporter": False,
                "advice_type": AdviceType.REFUSE,
            }
            url = reverse(
                "cases:generated_documents:generated_documents",
                kwargs={"pk": str(submitted_standard_application.pk)},
            )
            response = api_client.post(url, data=data, **gov_headers)
            assert response.status_code == 201, response.content

        url = reverse(
            "cases:finalise",
            kwargs={"pk": str(submitted_standard_application.pk)},
        )
        response = api_client.put(url, data={}, **gov_headers)
        assert response.status_code == 201, response.content

        return submitted_standard_application


@when(parsers.parse("the refused application is issued on appeal at {timestamp}"))
def when_the_application_is_issued_on_appeal_at(
    refused_application, api_client, lu_case_officer, lu_case_officer_headers, siel_template, timestamp
):
    with freeze_time(timestamp):
        refused_application.advice.filter(level=AdviceLevel.FINAL).update(
            type=AdviceType.APPROVE,
            text="issued on appeal",
        )

        url = reverse(
            "caseworker_applications:change_status",
            kwargs={
                "pk": str(refused_application.pk),
            },
        )
        response = api_client.post(
            url,
            data={"status": CaseStatusEnum.REOPENED_FOR_CHANGES},
            **lu_case_officer_headers,
        )
        assert response.status_code == 200, response.content
        refused_application.refresh_from_db()
        assert refused_application.status.status == CaseStatusEnum.REOPENED_FOR_CHANGES

        response = api_client.post(
            url,
            data={"status": CaseStatusEnum.UNDER_FINAL_REVIEW},
            **lu_case_officer_headers,
        )
        assert response.status_code == 200, response.content
        refused_application.refresh_from_db()
        assert refused_application.status.status == CaseStatusEnum.UNDER_FINAL_REVIEW

    with freeze_time(timestamp):
        data = {"action": AdviceType.APPROVE, "duration": 24}
        for good_on_app in refused_application.goods.all():
            good_on_app.quantity = 100
            good_on_app.value = 10000
            good_on_app.save()
            data[f"quantity-{good_on_app.id}"] = str(good_on_app.quantity)
            data[f"value-{good_on_app.id}"] = str(good_on_app.value)
            FinalAdviceFactory(user=lu_case_officer, case=refused_application, good=good_on_app.good)

            issue_date = datetime.datetime.fromisoformat(timestamp)
            data.update({"year": issue_date.year, "month": issue_date.month, "day": issue_date.day})

            refused_application.flags.remove(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

            url = reverse("applications:finalise", kwargs={"pk": refused_application.pk})
            response = api_client.put(url, data=data, **lu_case_officer_headers)
            assert response.status_code == 200, response.content
            response = response.json()

            with mock_aws():
                s3 = init_s3_client()
                s3.create_bucket(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    CreateBucketConfiguration={
                        "LocationConstraint": settings.AWS_REGION,
                    },
                )
                data = {
                    "template": str(siel_template.id),
                    "text": "",
                    "visible_to_exporter": False,
                    "advice_type": AdviceType.APPROVE,
                }
                url = reverse(
                    "cases:generated_documents:generated_documents",
                    kwargs={"pk": str(refused_application.pk)},
                )
                response = api_client.post(url, data=data, **lu_case_officer_headers)
                assert response.status_code == 201, response.content

            url = reverse(
                "cases:finalise",
                kwargs={"pk": str(refused_application.pk)},
            )
            response = api_client.put(url, data={}, **lu_case_officer_headers)
            assert response.status_code == 201


@when(parsers.parse("the issued application is revoked at {timestamp}"))
def when_the_issued_application_is_revoked(api_client, lu_sr_manager_headers, issued_application, timestamp):
    with freeze_time(timestamp):
        issued_licence = issued_application.licences.get()
        url = reverse("licences:licence_details", kwargs={"pk": str(issued_licence.pk)})
        response = api_client.patch(
            url,
            data={"status": LicenceStatus.REVOKED},
            **lu_sr_manager_headers,
        )
        assert response.status_code == 200, response.status_code


@then(parsers.parse("the application status is set to {status}"))
def then_the_application_status_is_set_to(submitted_standard_application, status):
    submitted_standard_application.refresh_from_db()

    assert (
        submitted_standard_application.status.status == status
    ), f"Application status is not {status} it is {submitted_standard_application.status.status}"


@then(parsers.parse("the application sub-status is set to {sub_status}"))
def then_the_application_status_is_set_to(submitted_standard_application, sub_status):
    submitted_standard_application.refresh_from_db()

    assert (
        submitted_standard_application.sub_status.name == sub_status
    ), f"Application sub-status status is not {sub_status} it is {submitted_standard_application.sub_status.name}"
