import pytest

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
from api.staticdata.statuses.enums import CaseStatusEnum


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
    submitted_application = StandardApplicationFactory(organisation=organisation)
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


@then("it will have the time of when the decision was made")
def licence_decision_time(licence_decisions_data, withdrawn_time):
    licence_decision = licence_decisions_data[0]
    assert licence_decision["decision_made_at"] == withdrawn_time
