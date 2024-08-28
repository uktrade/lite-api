import datetime
import pytest
import uuid

from django.utils import timezone
from django.urls import reverse
from freezegun import freeze_time
from pytest_bdd import (
    given,
    parsers,
    then,
    scenarios,
)
from rest_framework import status

from api.applications.tests.factories import StandardApplicationFactory
from api.cases.enums import (
    AdviceType,
    CaseTypeEnum,
)
from api.cases.tests.factories import FinalAdviceFactory
from api.cases.generated_documents.tests.factories import GeneratedCaseDocumentFactory
from api.letter_templates.tests.factories import LetterTemplateFactory
from api.staticdata.decisions.models import Decision
from api.staticdata.letter_layouts.tests.factories import LetterLayoutFactory
from api.staticdata.statuses.enums import (
    CaseStatusEnum,
    CaseSubStatusIdEnum,
)


scenarios("./scenarios/licence_decisions.feature")


@pytest.fixture()
def licence_decisions_list_url():
    return reverse("data_workspace:v2:dw-licence-decisions-list")


@pytest.fixture()
def withdrawn_time():
    with freeze_time("2024-01-01 12:00:01") as frozen_time:
        yield timezone.make_aware(frozen_time())


@given("a SIEL application that has been withdrawn by the exporter", target_fixture="application")
def withdrawn_siel_application(api_client, exporter_headers, organisation, withdrawn_time):
    submitted_application = StandardApplicationFactory(
        organisation=organisation,
        submitted_at=datetime.datetime.now(),
    )
    change_status_url = reverse(
        "exporter_applications:change_status",
        kwargs={
            "pk": str(submitted_application.pk),
        },
    )
    response = api_client.post(
        change_status_url,
        **exporter_headers,
        data={"status": CaseStatusEnum.WITHDRAWN},
    )
    assert response.status_code == status.HTTP_200_OK
    submitted_application.refresh_from_db()
    assert submitted_application.status.status == CaseStatusEnum.WITHDRAWN
    return submitted_application


@then(
    parsers.parse('there will be a licence decision of "{licence_decision_type}" for that application'),
    target_fixture="licence_decisions_data",
)
def licence_decision(licence_decision_type, unpage_data, licence_decisions_list_url, application):
    licence_decisions_data = unpage_data(licence_decisions_list_url)
    assert len(licence_decisions_data) == 1
    licence_decision = licence_decisions_data[0]
    assert licence_decision["application_id"] == str(application.pk)
    assert licence_decision["decision"] == licence_decision_type
    return licence_decisions_data


@then("the licence decision time will be the time of when the application was withdrawn")
def licence_decision_time(licence_decisions_data, withdrawn_time):
    licence_decision = licence_decisions_data[0]
    assert licence_decision["decision_made_at"] == withdrawn_time


@given("a SIEL application that has a licence issued", target_fixture="application")
def application_with_licence_issued(organisation, api_client, gov_headers, gov_user, issued_time):
    submitted_application = StandardApplicationFactory(
        organisation=organisation,
        submitted_at=datetime.datetime.now(),
    )
    finalise_application_url = reverse(
        "applications:finalise",
        kwargs={
            "pk": str(submitted_application.pk),
        },
    )
    post_date = timezone.now()
    response = api_client.put(
        finalise_application_url,
        data={
            "action": AdviceType.APPROVE,
            "year": post_date.year,
            "month": post_date.month,
            "day": post_date.day,
        },
        **gov_headers,
    )
    assert response.status_code == status.HTTP_200_OK, f"Error {response.json()['errors']} raised instead of 200"

    licence = submitted_application.licences.get()

    FinalAdviceFactory(
        case=submitted_application,
        user=gov_user,
        type=AdviceType.APPROVE,
    )
    letter_layout = LetterLayoutFactory(id=uuid.UUID(int=1))
    template = LetterTemplateFactory(
        layout=letter_layout,
    )
    template.case_types.set([CaseTypeEnum.SIEL.id])
    template.decisions.set([Decision.objects.get(name=AdviceType.APPROVE)])
    GeneratedCaseDocumentFactory(
        advice_type=AdviceType.APPROVE,
        case=submitted_application.get_case(),
        licence=licence,
        template=template,
    )

    finalise_case_url = reverse(
        "cases:finalise",
        kwargs={
            "pk": str(submitted_application.pk),
        },
    )
    response = api_client.put(
        finalise_case_url,
        data={},
        **gov_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED, f"Error {response.json()['errors']} raised instead of 201"
    submitted_application.refresh_from_db()
    assert submitted_application.status.status == CaseStatusEnum.FINALISED
    assert str(submitted_application.sub_status.pk) == CaseSubStatusIdEnum.FINALISED__APPROVED
    return submitted_application


@pytest.fixture()
def issued_time():
    with freeze_time("2024-01-01 12:00:01") as frozen_time:
        yield timezone.make_aware(frozen_time())


@then("the licence decision time will be the time of when the licence was issued")
def application_with_licence_issued(licence_decisions_data, issued_time):
    licence_decision = licence_decisions_data[0]
    assert licence_decision["decision_made_at"] == issued_time


@pytest.fixture()
def refused_time():
    with freeze_time("2024-01-01 12:00:01") as frozen_time:
        yield timezone.make_aware(frozen_time())


@given("a SIEL application that has a licence refused", target_fixture="application")
def application_with_licence_refused(organisation, api_client, gov_headers, gov_user, refused_time):
    submitted_application = StandardApplicationFactory(
        organisation=organisation,
        submitted_at=datetime.datetime.now(),
    )
    finalise_application_url = reverse(
        "applications:finalise",
        kwargs={
            "pk": str(submitted_application.pk),
        },
    )
    post_date = timezone.now()
    response = api_client.put(
        finalise_application_url,
        data={
            "action": AdviceType.REFUSE,
            "year": post_date.year,
            "month": post_date.month,
            "day": post_date.day,
        },
        **gov_headers,
    )
    assert response.status_code == status.HTTP_200_OK, f"Error {response.json()['errors']} raised instead of 200"

    FinalAdviceFactory(
        case=submitted_application,
        user=gov_user,
        type=AdviceType.REFUSE,
    )
    letter_layout = LetterLayoutFactory(id=uuid.UUID(int=1))
    template = LetterTemplateFactory(
        layout=letter_layout,
    )
    template.case_types.set([CaseTypeEnum.SIEL.id])
    template.decisions.set([Decision.objects.get(name=AdviceType.REFUSE)])
    GeneratedCaseDocumentFactory(
        advice_type=AdviceType.REFUSE,
        case=submitted_application.get_case(),
        template=template,
    )

    finalise_case_url = reverse(
        "cases:finalise",
        kwargs={
            "pk": str(submitted_application.pk),
        },
    )
    response = api_client.put(
        finalise_case_url,
        data={},
        **gov_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    submitted_application.refresh_from_db()
    assert submitted_application.status.status == CaseStatusEnum.FINALISED
    assert str(submitted_application.sub_status.pk) == CaseSubStatusIdEnum.FINALISED__REFUSED
    return submitted_application


@then("the licence decision time will be the time of when the licence was refused")
def application_with_licence_issued(licence_decisions_data, refused_time):
    licence_decision = licence_decisions_data[0]
    assert licence_decision["decision_made_at"] == refused_time


@pytest.fixture()
def nlr_time():
    with freeze_time("2024-01-01 12:00:01") as frozen_time:
        yield timezone.make_aware(frozen_time())


@given("a SIEL application that is NLR", target_fixture="application")
def nlr_siel_application(gov_user, organisation, api_client, gov_headers, nlr_time):
    submitted_application = StandardApplicationFactory(
        organisation=organisation,
        submitted_at=datetime.datetime.now(),
    )
    FinalAdviceFactory(user=gov_user, case=submitted_application, type=AdviceType.NO_LICENCE_REQUIRED)
    letter_layout = LetterLayoutFactory(id=uuid.UUID(int=1))
    template = LetterTemplateFactory(
        layout=letter_layout,
    )
    template.case_types.set([CaseTypeEnum.SIEL.id])
    template.decisions.set([Decision.objects.get(name=AdviceType.NO_LICENCE_REQUIRED)])
    GeneratedCaseDocumentFactory(
        advice_type=AdviceType.NO_LICENCE_REQUIRED,
        case=submitted_application.get_case(),
        template=template,
    )

    finalise_case_url = reverse(
        "cases:finalise",
        kwargs={
            "pk": str(submitted_application.pk),
        },
    )
    response = api_client.put(
        finalise_case_url,
        data={},
        **gov_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED

    return submitted_application


@then("the licence decision time will be the time of when a decision of no licence needed was made")
def nlr_licence_decision_time(licence_decisions_data, nlr_time):
    licence_decision = licence_decisions_data[0]
    assert licence_decision["decision_made_at"] == nlr_time
