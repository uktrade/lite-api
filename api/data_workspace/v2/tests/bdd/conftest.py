import datetime
import json
import uuid

import pytest
import pytz
from dateutil.parser import parse
from django.conf import settings
from django.urls import reverse
from freezegun import freeze_time
from moto import mock_aws
from operator import itemgetter
from pytest_bdd import (
    given,
    parsers,
    then,
    when,
)
from rest_framework import status
from rest_framework.test import APIClient

from api.applications.enums import ApplicationExportType
from api.applications.models import PartyOnApplication
from api.applications.tests.factories import (
    DraftStandardApplicationFactory,
    GoodOnApplicationFactory,
    PartyOnApplicationFactory,
    StandardApplicationFactory,
)
from api.cases.celery_tasks import update_cases_sla
from api.cases.enums import (
    AdviceLevel,
    AdviceType,
    CaseTypeEnum,
)
from api.cases.models import (
    CaseType,
    LicenceDecision,
)
from api.cases.tests.factories import FinalAdviceFactory
from api.core.constants import (
    ExporterPermissions,
    GovPermissions,
    Roles,
)
from api.documents.libraries.s3_operations import init_s3_client
from api.flags.enums import SystemFlags
from api.goods.tests.factories import GoodFactory
from api.letter_templates.models import LetterTemplate
from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from api.licences.tests.factories import (
    GoodOnLicenceFactory,
    StandardLicenceFactory,
)
from api.organisations.tests.factories import OrganisationFactory
from api.parties.enums import PartyType
from api.parties.tests.factories import PartyDocumentFactory
from api.staticdata.countries.models import Country
from api.staticdata.letter_layouts.models import LetterLayout
from api.staticdata.report_summaries.models import (
    ReportSummaryPrefix,
    ReportSummarySubject,
)
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.units.enums import Units
from api.users.enums import (
    SystemUser,
    UserType,
)
from api.users.libraries.user_to_token import user_to_token
from api.users.models import (
    BaseUser,
    Permission,
)
from api.users.tests.factories import (
    BaseUserFactory,
    ExporterUserFactory,
    GovUserFactory,
    RoleFactory,
    UserOrganisationRelationshipFactory,
)


@pytest.fixture()
def standard_draft_licence():
    application = StandardApplicationFactory(
        status=CaseStatus.objects.get(status=CaseStatusEnum.FINALISED),
    )
    good = GoodFactory(organisation=application.organisation)
    good_on_application = GoodOnApplicationFactory(
        application=application, good=good, quantity=100.0, value=1500, unit=Units.NAR
    )
    licence = StandardLicenceFactory(case=application, status=LicenceStatus.DRAFT)
    GoodOnLicenceFactory(
        good=good_on_application,
        quantity=good_on_application.quantity,
        usage=0.0,
        value=good_on_application.value,
        licence=licence,
    )
    return licence


@pytest.fixture()
def standard_licence():
    application = StandardApplicationFactory(
        status=CaseStatus.objects.get(status=CaseStatusEnum.FINALISED),
    )
    party_on_application = PartyOnApplicationFactory(application=application)
    good = GoodFactory(organisation=application.organisation)
    good_on_application = GoodOnApplicationFactory(
        application=application, good=good, quantity=100.0, value=1500, unit=Units.NAR
    )
    licence = StandardLicenceFactory(case=application, status=LicenceStatus.DRAFT)
    GoodOnLicenceFactory(
        good=good_on_application,
        quantity=good_on_application.quantity,
        usage=0.0,
        value=good_on_application.value,
        licence=licence,
    )
    licence.status = LicenceStatus.ISSUED
    licence.save()
    return licence


@pytest.fixture()
def standard_case_with_final_advice(lu_case_officer):
    case = StandardApplicationFactory(
        status=CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW),
    )
    good = GoodFactory(organisation=case.organisation)
    good_on_application = GoodOnApplicationFactory(
        application=case, good=good, quantity=100.0, value=1500, unit=Units.NAR
    )
    FinalAdviceFactory(user=lu_case_officer, case=case, good=good_on_application.good)
    return case


@pytest.fixture()
def standard_case_with_refused_advice(lu_case_officer, standard_case_with_final_advice):
    final_advice = standard_case_with_final_advice.advice.filter(level=AdviceLevel.FINAL)
    for advice in final_advice:
        advice.type = AdviceType.REFUSE
        advice.text = "refusing licence"
        advice.denial_reasons.set(["1a", "1b", "1c"])
        advice.save()
    return standard_case_with_final_advice


@pytest.fixture()
def licence_with_deleted_party(standard_licence):
    licence = standard_licence
    application = licence.case.baseapplication
    old_party_on_application = PartyOnApplication.objects.get(application=application)
    new_party_on_application = PartyOnApplicationFactory(application=application)
    old_party_on_application.delete()
    return licence


def load_json(filename):
    with open(filename) as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def mock_s3():
    with mock_aws():
        s3 = init_s3_client()
        s3.create_bucket(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            CreateBucketConfiguration={
                "LocationConstraint": settings.AWS_REGION,
            },
        )
        yield


@pytest.fixture()
def seed_layouts():
    layouts = load_json("api/data_workspace/v2/tests/bdd/initial_data/letter_layouts.json")
    for layout in layouts:
        LetterLayout.objects.get_or_create(**layout)


@pytest.fixture()
def seed_templates(seed_layouts):
    # if this template exists the seed command is executed and all templates are seeded
    if LetterTemplate.objects.filter(name="SIEL template").exists():
        return

    templates = load_json("api/data_workspace/v2/tests/bdd/initial_data/letter_templates.json")
    for template in templates:
        template_instance, _ = LetterTemplate.objects.get_or_create(**template)
        template_instance.case_types.add(CaseType.objects.get(id=CaseTypeEnum.SIEL.id))


@pytest.fixture()
def siel_template(seed_templates):
    return LetterTemplate.objects.get(layout_id="00000000-0000-0000-0000-000000000001")


@pytest.fixture()
def siel_refusal_template(seed_templates):
    return LetterTemplate.objects.get(layout_id="00000000-0000-0000-0000-000000000006")


@pytest.fixture(autouse=True)
def system_user(db):
    if BaseUser.objects.filter(id=SystemUser.id).exists():
        return BaseUser.objects.get(id=SystemUser.id)
    else:
        return BaseUserFactory(id=SystemUser.id)


@pytest.fixture()
def gov_user():
    return GovUserFactory()


@pytest.fixture()
def lu_user():
    return GovUserFactory()


@pytest.fixture()
def gov_user_permissions():
    for permission in GovPermissions:
        Permission.objects.get_or_create(id=permission.name, name=permission.value, type=UserType.INTERNAL.value)


@pytest.fixture()
def ogd_advisor(gov_user, gov_user_permissions):
    gov_user.role = RoleFactory(name="OGD Advisor", type=UserType.INTERNAL)
    gov_user.role.permissions.set(
        [
            GovPermissions.MAINTAIN_FOOTNOTES.name,
        ]
    )
    gov_user.save()
    return gov_user


@pytest.fixture()
def lu_case_officer(gov_user, gov_user_permissions):
    gov_user.role = RoleFactory(name="Case officer", type=UserType.INTERNAL)
    gov_user.role.permissions.set(
        [
            GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
            GovPermissions.MANAGE_LICENCE_DURATION.name,
            GovPermissions.REOPEN_CLOSED_CASES.name,
        ]
    )
    gov_user.save()
    return gov_user


@pytest.fixture()
def lu_senior_manager(lu_user, gov_user_permissions):
    lu_user.role = RoleFactory(
        id=Roles.INTERNAL_LU_SENIOR_MANAGER_ROLE_ID, name="LU Senior Manager", type=UserType.INTERNAL
    )
    lu_user.role.permissions.set(
        [GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name, GovPermissions.MANAGE_LICENCE_DURATION.name]
    )
    lu_user.save()
    return lu_user


@pytest.fixture()
def gov_headers(gov_user):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}


@pytest.fixture()
def ogd_advisor_headers(ogd_advisor):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(ogd_advisor.baseuser_ptr)}


@pytest.fixture()
def lu_case_officer_headers(lu_case_officer):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(lu_case_officer.baseuser_ptr)}


@pytest.fixture()
def lu_sr_manager_headers(lu_senior_manager):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(lu_senior_manager.baseuser_ptr)}


@pytest.fixture()
def exporter_user():
    return ExporterUserFactory()


@pytest.fixture()
def exporter_user_permissions():
    for permission in ExporterPermissions:
        Permission.objects.get_or_create(id=permission.name, name=permission.value, type=UserType.EXPORTER.value)


@pytest.fixture()
def organisation(exporter_user_permissions, exporter_user):
    organisation = OrganisationFactory()

    UserOrganisationRelationshipFactory(
        organisation=organisation,
        role__permissions=[ExporterPermissions.SUBMIT_LICENCE_APPLICATION.name],
        user=exporter_user,
    )

    return organisation


@pytest.fixture()
def exporter_headers(exporter_user, organisation):
    return {
        "HTTP_EXPORTER_USER_TOKEN": user_to_token(exporter_user.baseuser_ptr),
        "HTTP_ORGANISATION_ID": str(organisation.id),
    }


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def unpage_data(api_client):
    def _unpage_data(url):
        unpaged_results = []
        while True:
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            unpaged_results += response.json()["results"]
            if not response.data["next"]:
                break
            url = response.data["next"]

        return unpaged_results

    return _unpage_data


@pytest.fixture()
def parse_attributes(parse_table):
    def _parse_attributes(attributes):
        kwargs = {}
        table_data = parse_table(attributes)
        for key, value in table_data[1:]:
            kwargs[key] = value
        return kwargs

    return _parse_attributes


@pytest.fixture()
def standard_application():
    application = StandardApplicationFactory(
        status=CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW),
    )
    party_on_application = PartyOnApplicationFactory(application=application)
    good = GoodFactory(organisation=application.organisation)
    good_on_application = GoodOnApplicationFactory(
        application=application, good=good, quantity=100.0, value=1500, unit=Units.NAR
    )
    return application


@pytest.fixture()
def draft_application():
    draft_application = DraftStandardApplicationFactory()
    return draft_application


def run_processing_time_task(start, up_to):
    processing_time_task_run_date_time = start.replace(hour=22, minute=30)
    up_to = pytz.utc.localize(datetime.datetime.fromisoformat(up_to))
    while processing_time_task_run_date_time <= up_to:
        with freeze_time(processing_time_task_run_date_time):
            update_cases_sla()
        processing_time_task_run_date_time = processing_time_task_run_date_time + datetime.timedelta(days=1)


@pytest.fixture
def submit_application(api_client, exporter_headers, mocker):
    def _submit_application(draft_application):
        type_code = "T" if draft_application.export_type == ApplicationExportType.TEMPORARY else "P"
        reference_code = f"GBSIEL/2024/0000001/{type_code}"
        mocker.patch("api.cases.models.Case.generate_reference_code", return_value=reference_code)

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


@given(parsers.parse("a consignee added to the application in `{country}`"))
def add_consignee_to_application(draft_standard_application, country):
    consignee = draft_standard_application.parties.get(party__type=PartyType.CONSIGNEE)
    consignee.party.country = Country.objects.get(name=country)
    consignee.party.save()


@given(parsers.parse("an end-user added to the application of `{country}`"))
def add_end_user_to_application(draft_standard_application, country):
    end_user = draft_standard_application.parties.get(party__type=PartyType.END_USER)
    end_user.party.country = Country.objects.get(name=country)
    end_user.party.save()


@when(
    "the application is submitted",
    target_fixture="submitted_standard_application",
)
def when_the_application_is_submitted(submit_application, draft_standard_application):
    return submit_application(draft_standard_application)


@then(parsers.parse("the `{table_name}` table is empty"))
def empty_table(client, unpage_data, table_name):
    metadata_url = reverse("data_workspace:v2:table-metadata")
    response = client.get(metadata_url)
    tables_metadata = response.json()["tables"]
    for m in tables_metadata:
        if m["table_name"] == table_name:
            table_metadata = m
            break
    else:
        pytest.fail(f"No table called {table_name} found")

    table_data = unpage_data(table_metadata["endpoint"])

    assert table_data == [], f"`{table_name}` table should be empty"


@pytest.fixture()
def parse_table():
    def _parse_table(data_table):
        lines = data_table.strip().split("\n")
        rows = []
        for line in lines:
            values = [value.strip() for value in line.split("|") if value]
            rows.append(values)
        return rows

    return _parse_table


def cast_to_types(data, fields_metadata):
    fields_metadata = {field["name"]: field for field in fields_metadata}

    cast_data = []
    for row in data:
        cast_row = row.copy()
        for key, value in cast_row.items():
            if not value:
                continue
            field_metadata = fields_metadata[key]
            if value == "NULL":
                cast_row[key] = None
            elif field_metadata["type"] == "Integer":
                cast_row[key] = int(value)
            elif field_metadata["type"] == "Float":
                cast_row[key] = float(value)
            elif field_metadata["type"] == "DateTime":
                cast_row[key] = pytz.utc.localize(parse(value, ignoretz=True))
            elif field_metadata["type"] == "UUID":
                cast_row[key] = uuid.UUID(value) if value != "None" else None
        cast_data.append(cast_row)

    return cast_data


@then(parsers.parse("the `{table_name}` table has the following rows:{rows}"))
def check_rows(client, parse_table, unpage_data, table_name, rows):
    metadata_url = reverse("data_workspace:v2:table-metadata")
    response = client.get(metadata_url)
    tables_metadata = response.json()["tables"]
    for m in tables_metadata:
        if m["table_name"] == table_name:
            table_metadata = m
            break
    else:
        pytest.fail(f"No table called {table_name} found")

    actual_data = unpage_data(table_metadata["endpoint"])
    actual_data = cast_to_types(actual_data, table_metadata["fields"])
    parsed_rows = parse_table(rows)
    keys = parsed_rows[0]
    expected_data = []
    for row in parsed_rows[1:]:
        expected_data.append({key: value for key, value in zip(keys, row)})
    expected_data = cast_to_types(expected_data, table_metadata["fields"])
    actual_data = sorted(actual_data, key=itemgetter(*keys))
    expected_data = sorted(expected_data, key=itemgetter(*keys))
    assert actual_data == expected_data


@when(
    parsers.parse("the application is submitted at {submission_time}"),
    target_fixture="submitted_standard_application",
)
def when_the_application_is_submitted_at(submit_application, draft_standard_application, submission_time):
    with freeze_time(submission_time):
        return submit_application(draft_standard_application)


@given(parsers.parse("LITE exports `{table_name}` data to DW"))
def given_endpoint_exists(client, table_name):
    metadata_url = reverse("data_workspace:v2:table-metadata")
    response = client.get(metadata_url)
    assert table_name in [t["table_name"] for t in response.json()["tables"]]


@given(parsers.parse("the application has the following goods:{goods}"))
def given_the_application_has_the_following_goods(parse_table, draft_standard_application, goods):
    draft_standard_application.goods.all().delete()

    good_attributes = parse_table(goods)
    keys = good_attributes[0]
    for row in good_attributes[1:]:
        data = dict(zip(keys, row))
        GoodOnApplicationFactory(
            application=draft_standard_application,
            id=data["id"],
            good__name=data["name"],
            quantity=float(data.get("quantity", "10.0")),
            unit=data.get("unit", "NAR"),
            value=float(data.get("value", "100.0")),
        )


@when(parsers.parse("the goods are assessed by TAU as:{assessments}"))
def when_the_goods_are_assessed_by_tau(
    parse_table,
    submitted_standard_application,
    assessments,
    api_client,
    lu_case_officer,
    gov_headers,
):
    assessments = parse_table(assessments)[1:]
    url = reverse("assessments:make_assessments", kwargs={"case_pk": submitted_standard_application.pk})

    assessment_payload = []
    for good_on_application_id, control_list_entry, report_summary_prefix, report_summary_subject in assessments:
        data = {
            "id": good_on_application_id,
            "comment": "Some comment",
        }

        if control_list_entry == "NLR":
            data.update(
                {
                    "control_list_entries": [],
                    "is_good_controlled": False,
                }
            )
        else:
            if report_summary_prefix:
                prefix = ReportSummaryPrefix.objects.get(name=report_summary_prefix)
            else:
                prefix = None
            subject = ReportSummarySubject.objects.get(name=report_summary_subject)
            data.update(
                {
                    "control_list_entries": [control_list_entry],
                    "report_summary_prefix": prefix.pk if prefix else None,
                    "report_summary_subject": subject.pk,
                    "is_good_controlled": True,
                    "regime_entries": [],
                }
            )
        assessment_payload.append(data)

    response = api_client.put(
        url,
        assessment_payload,
        **gov_headers,
    )
    assert response.status_code == 200, response.content


@given(
    parsers.parse("a draft standard application with attributes:{attributes}"),
    target_fixture="draft_standard_application",
)
def given_a_draft_standard_application_with_attributes(organisation, parse_attributes, attributes):
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


@pytest.fixture()
def issue_licence(api_client, lu_case_officer, gov_headers, siel_template):
    def _issue_licence(application):
        data = {"action": AdviceType.APPROVE, "duration": 24}
        for good_on_app in application.goods.all():
            good_on_app.quantity = 100
            good_on_app.value = 10000
            good_on_app.save()
            data[f"quantity-{good_on_app.id}"] = str(good_on_app.quantity)
            data[f"value-{good_on_app.id}"] = str(good_on_app.value)
            # create final advice for controlled goods; skip NLR goods
            if good_on_app.is_good_controlled == False:
                continue
            FinalAdviceFactory(user=lu_case_officer, case=application, good=good_on_app.good)

        issue_date = datetime.datetime.now()
        data.update({"year": issue_date.year, "month": issue_date.month, "day": issue_date.day})

        application.flags.remove(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

        url = reverse("applications:finalise", kwargs={"pk": application.pk})
        response = api_client.put(url, data=data, **gov_headers)
        assert response.status_code == 200, response.content
        response = response.json()

        data = {
            "template": str(siel_template.id),
            "text": "",
            "visible_to_exporter": False,
            "advice_type": AdviceType.APPROVE,
        }
        url = reverse(
            "cases:generated_documents:generated_documents",
            kwargs={"pk": str(application.pk)},
        )
        response = api_client.post(url, data=data, **gov_headers)
        assert response.status_code == 201, response.content

        url = reverse(
            "cases:finalise",
            kwargs={"pk": str(application.pk)},
        )
        response = api_client.put(url, data={}, **gov_headers)
        assert response.status_code == 201

    return _issue_licence


@pytest.fixture()
def reopen_application(
    caseworker_change_status,
):
    def _reopen_application(application):
        caseworker_change_status(application, CaseStatusEnum.REOPENED_FOR_CHANGES)

    return _reopen_application


@pytest.fixture()
def refuse_application(
    api_client,
    lu_case_officer,
    siel_refusal_template,
    gov_headers,
):
    def _refuse_application(application, denial_reasons=None):
        if not denial_reasons:
            denial_reasons = ["1a", "1b", "1c"]

        # delete previous final advice if any before we change decision
        application.advice.filter(level=AdviceLevel.FINAL).delete()

        data = {"action": AdviceType.REFUSE}
        for good_on_app in application.goods.all():
            good_on_app.quantity = 100
            good_on_app.value = 10000
            good_on_app.save()
            data[f"quantity-{good_on_app.id}"] = str(good_on_app.quantity)
            data[f"value-{good_on_app.id}"] = str(good_on_app.value)
            FinalAdviceFactory(
                user=lu_case_officer,
                case=application,
                good=good_on_app.good,
                type=AdviceType.REFUSE,
                denial_reasons=denial_reasons,
            )

        application.flags.remove(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

        url = reverse("applications:finalise", kwargs={"pk": application.pk})
        response = api_client.put(url, data=data, **gov_headers)
        assert response.status_code == 200, response.content
        response = response.json()

        data = {
            "template": str(siel_refusal_template.id),
            "text": "",
            "visible_to_exporter": False,
            "advice_type": AdviceType.REFUSE,
        }
        url = reverse(
            "cases:generated_documents:generated_documents",
            kwargs={"pk": str(application.pk)},
        )
        response = api_client.post(url, data=data, **gov_headers)
        assert response.status_code == 201, response.content

        url = reverse(
            "cases:finalise",
            kwargs={"pk": str(application.pk)},
        )
        response = api_client.put(url, data={}, **gov_headers)
        assert response.status_code == 201, response.content

        application.refresh_from_db()

    return _refuse_application


@when(parsers.parse("the application is issued at {timestamp}"), target_fixture="issued_application")
def when_the_application_is_issued_at(
    issue_licence,
    submitted_standard_application,
    timestamp,
    mocker,
):
    run_processing_time_task(submitted_standard_application.submitted_at, timestamp)

    def mock_licence_save(self, *args, send_status_change_to_hmrc=False, **kwargs):
        self.id = "1b2f95c3-9cd2-4dee-b134-a79786f78c06"
        self.end_date = datetime.datetime.now().date()
        super(Licence, self).save(*args, **kwargs)

    mocker.patch.object(Licence, "save", mock_licence_save)

    def mock_licence_decision_save(self, *args, **kwargs):
        self.id = "ebd27511-7be3-4e5c-9ce9-872ad22811a1"
        super(LicenceDecision, self).save(*args, **kwargs)

    mocker.patch.object(LicenceDecision, "save", mock_licence_decision_save)

    with freeze_time(timestamp):
        issue_licence(submitted_standard_application)

    submitted_standard_application.refresh_from_db()
    issued_application = submitted_standard_application

    return issued_application


@when(parsers.parse("the application is re-opened at {timestamp}"))
def when_the_application_is_reopened_at(
    submitted_standard_application,
    reopen_application,
    timestamp,
):
    with freeze_time(timestamp):
        reopen_application(submitted_standard_application)


@when(parsers.parse("the application is refused at {timestamp}"), target_fixture="refused_application")
def when_the_application_is_refused_at(
    submitted_standard_application,
    refuse_application,
    timestamp,
    mocker,
):
    run_processing_time_task(submitted_standard_application.submitted_at, timestamp)

    def mock_licence_decision_refuse(self, *args, **kwargs):
        self.id = "4ea4261f-03f2-4baf-8784-5ec4b352d358"
        super(LicenceDecision, self).save(*args, **kwargs)

    mocker.patch.object(LicenceDecision, "save", mock_licence_decision_refuse)

    with freeze_time(timestamp):
        refuse_application(submitted_standard_application)

    submitted_standard_application.refresh_from_db()
    refused_application = submitted_standard_application

    return refused_application


@when(parsers.parse("the issued application is revoked at {timestamp}"))
def when_the_issued_application_is_revoked(
    api_client,
    lu_sr_manager_headers,
    issued_application,
    timestamp,
    mocker,
):
    run_processing_time_task(issued_application.submitted_at, timestamp)

    def mock_licence_decision_revoke(self, *args, **kwargs):
        self.id = "65ad0aa8-64ad-4805-92f1-86a4874e9fe6"
        super(LicenceDecision, self).save(*args, **kwargs)

    mocker.patch.object(LicenceDecision, "save", mock_licence_decision_revoke)

    with freeze_time(timestamp):
        issued_licence = issued_application.licences.get()
        url = reverse("licences:licence_details", kwargs={"pk": str(issued_licence.pk)})
        response = api_client.patch(
            url,
            data={"status": LicenceStatus.REVOKED},
            **lu_sr_manager_headers,
        )
        assert response.status_code == 200, response.status_code


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


@when(parsers.parse("the refused application is issued on appeal at {timestamp}"), target_fixture="issued_application")
def when_the_application_is_issued_on_appeal_at(
    appealed_application,
    timestamp,
    caseworker_change_status,
    issue_licence,
    mocker,
):
    run_processing_time_task(appealed_application.appeal.created_at, timestamp)

    def mock_licence_save_on_appeal(self, *args, send_status_change_to_hmrc=False, **kwargs):
        self.id = "4106ced1-b2b9-41e8-ad42-47c36b07b345"  # /PS-IGNORE
        self.end_date = datetime.datetime.now().date()
        super(Licence, self).save(*args, **kwargs)

    mocker.patch.object(Licence, "save", mock_licence_save_on_appeal)

    def mock_licence_decision_appeal(self, *args, **kwargs):
        self.id = "f0bc0c1e-c9c5-4a90-b4c8-81a7f3cbe1e7"  # /PS-IGNORE
        super(LicenceDecision, self).save(*args, **kwargs)

    mocker.patch.object(LicenceDecision, "save", mock_licence_decision_appeal)

    with freeze_time(timestamp):
        appealed_application.advice.filter(level=AdviceLevel.FINAL).update(
            type=AdviceType.APPROVE,
            text="issued on appeal",
        )

        caseworker_change_status(appealed_application, CaseStatusEnum.REOPENED_FOR_CHANGES)
        caseworker_change_status(appealed_application, CaseStatusEnum.UNDER_FINAL_REVIEW)
        issue_licence(appealed_application)

    appealed_application.refresh_from_db()
    issued_application = appealed_application

    return issued_application


@when(parsers.parse("the application is reissued at {timestamp}"))
def when_the_application_is_issued_again_at(
    issued_application,
    timestamp,
    caseworker_change_status,
    issue_licence,
    mocker,
):
    run_processing_time_task(issued_application.appeal.created_at, timestamp)

    def mock_licence_save_reissue(self, *args, send_status_change_to_hmrc=False, **kwargs):
        if self.status == LicenceStatus.CANCELLED:
            return
        self.id = "27b79b32-1ce8-45a3-b7eb-18947bed2fcb"  # PS-IGNORE
        self.end_date = datetime.datetime.now().date()
        super(Licence, self).save(*args, **kwargs)

    mocker.patch.object(Licence, "save", mock_licence_save_reissue)

    def mock_licence_decision_reissue(self, *args, **kwargs):
        self.id = "5c821bf0-a60a-43ec-b4a0-2280f40f9995"  # /PS-IGNORE
        super(LicenceDecision, self).save(*args, **kwargs)

    mocker.patch.object(LicenceDecision, "save", mock_licence_decision_reissue)

    with freeze_time(timestamp):
        issued_application.advice.filter(level=AdviceLevel.FINAL).update(
            type=AdviceType.APPROVE,
            text="reissuing the licence",
        )

        caseworker_change_status(issued_application, CaseStatusEnum.REOPENED_FOR_CHANGES)
        caseworker_change_status(issued_application, CaseStatusEnum.UNDER_FINAL_REVIEW)
        issue_licence(issued_application)
