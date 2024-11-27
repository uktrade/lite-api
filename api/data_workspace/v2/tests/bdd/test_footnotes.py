import pytest

from pytest_bdd import (
    parsers,
    scenarios,
    when,
)

from django.urls import reverse

from api.staticdata.statuses.enums import CaseStatusEnum
from api.teams.models import Team


scenarios("./scenarios/footnotes.feature")


@pytest.fixture()
def add_recommendation(
    api_client,
    ogd_advisor,
    ogd_advisor_headers,
):
    def _add_recommendation(application, footnotes_data):

        url = reverse("caseworker_applications:change_status", kwargs={"pk": str(application.pk)})
        response = api_client.post(url, data={"status": CaseStatusEnum.OGD_ADVICE}, **ogd_advisor_headers)
        assert response.status_code == 200

        ogd_advisor.team = Team.objects.get(name=footnotes_data[0]["team"])
        ogd_advisor.save()

        subjects = [("good_id", good_on_application.good.id) for good_on_application in application.goods.all()] + [
            (poa.party.type, poa.party.id) for poa in application.parties.all()
        ]

        data = [
            {
                "type": "approve",
                "text": "Recommend issuing licence",
                "proviso": "",
                "footnote_required": True,
                "footnote": footnotes_data[0]["footnotes"],
                subject_name: str(subject_id),
                "denial_reasons": [],
            }
            for subject_name, subject_id in subjects
        ]
        url = reverse("cases:user_advice", kwargs={"pk": str(application.pk)})
        response = api_client.post(url, data=data, **ogd_advisor_headers)
        assert response.status_code == 201

    return _add_recommendation


@when(parsers.parse("a recommendation is added with footnotes:{footnotes}"))
def when_a_recommendation_is_added_with_footnotes(
    submitted_standard_application, add_recommendation, parse_table, footnotes
):
    footnotes_data = [{"team": team, "footnotes": text} for team, text in parse_table(footnotes)[1:]]
    add_recommendation(submitted_standard_application, footnotes_data)
