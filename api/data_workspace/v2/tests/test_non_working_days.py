import pytest

from dateutil import parser
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


scenarios("./scenarios/non_working_days.feature")


@pytest.fixture()
def non_working_days_url():
    return reverse("data_workspace:dw-non-working-days-list")


@given(parsers.parse("{weekday_date} is a weekday"), target_fixture="scenario_date")
def is_weekday(weekday_date, mocker):
    weekday_date = parser.parse(weekday_date)

    mock_is_bank_holiday = mocker.patch("api.data_workspace.v2.views.is_bank_holiday")
    mock_is_bank_holiday.return_value = False

    mock_is_weekend = mocker.patch("api.data_workspace.v2.views.is_weekend")
    mock_is_weekend.return_value = False

    return weekday_date.date()


@given(parsers.parse("{bank_holiday_date} is a bank holiday"), target_fixture="scenario_date")
def is_bank_holiday(bank_holiday_date, mocker):
    bank_holiday_date = parser.parse(bank_holiday_date)

    mock_is_bank_holiday = mocker.patch("api.data_workspace.v2.views.is_bank_holiday")
    mock_is_bank_holiday.side_effect = lambda d: d == bank_holiday_date

    mock_is_weekend = mocker.patch("api.data_workspace.v2.views.is_weekend")
    mock_is_weekend.return_value = False

    return bank_holiday_date.date()


@given(parsers.parse("{weekend_date} falls on a weekend"), target_fixture="scenario_date")
def is_weekend(weekend_date, mocker):
    weekend_date = parser.parse(weekend_date)

    mock_is_bank_holiday = mocker.patch("api.data_workspace.v2.views.is_bank_holiday")
    mock_is_bank_holiday.return_value = False

    mock_is_weekend = mocker.patch("api.data_workspace.v2.views.is_weekend")
    mock_is_weekend.side_effect = lambda d: d == weekend_date

    return weekend_date.date()


@given(parsers.parse("the first application was created on {application_created_date}"))
def create_first_application(application_created_date):
    application_created_date = parser.parse(application_created_date)
    StandardApplicationFactory(
        created_at=application_created_date,
    )


@given(parsers.parse("the current date is {current_date}"))
def set_current_date(current_date):
    with freeze_time(current_date):
        yield current_date


@then(parsers.parse("{non_working_day_date} is not a non-working day"))
def weekday_should_not_be_sent_to_data_workspace(non_working_day_date, scenario_date, non_working_days_url, client):
    non_working_day_date = parser.parse(non_working_day_date).date()
    assert scenario_date == non_working_day_date, "The dates in the scenario don't match"

    response = client.get(non_working_days_url)

    assert response.status_code == status.HTTP_200_OK
    assert {"date": non_working_day_date, "type": "WEEKEND"} not in response.data
    assert {"date": non_working_day_date, "type": "BANK_HOLIDAY"} not in response.data


@then(parsers.parse("{non_working_day_date} is a non-working day"), target_fixture="found_non_working_day_type")
def is_non_working_day(non_working_day_date, scenario_date, non_working_days_url, client):
    non_working_day_date = parser.parse(non_working_day_date).date()
    assert non_working_day_date == scenario_date, "The dates in the scenario don't match"

    response = client.get(non_working_days_url)

    assert response.status_code == status.HTTP_200_OK

    found_dates = [(d["type"]) for d in response.data if d["date"] == non_working_day_date]
    assert len(found_dates) == 1

    return found_dates[0]


@then("is classified as a weekend")
def is_classified_as_a_weekend(found_non_working_day_type):
    assert found_non_working_day_type == "WEEKEND"


@then("is classified as a bank holiday")
def is_classified_as_a_bank_holiday(found_non_working_day_type):
    assert found_non_working_day_type == "BANK_HOLIDAY"


@then(parsers.parse("{unclassified_date} is not classified"))
def date_is_not_classified(unclassified_date, scenario_date, non_working_days_url, client):
    unclassified_date = parser.parse(unclassified_date).date()
    assert unclassified_date == scenario_date, "The dates in the scenario don't match"

    response = client.get(non_working_days_url)

    assert response.status_code == status.HTTP_200_OK
    assert {"date": scenario_date, "type": "WEEKEND"} not in response.data
    assert {"date": scenario_date, "type": "BANK_HOLIDAY"} not in response.data
