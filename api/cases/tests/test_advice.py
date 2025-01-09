import pytest

from api.cases.enums import AdviceLevel
from api.cases.tests.factories import FinalAdviceFactory

pytestmark = pytest.mark.django_db


def test_user_cannot_give_final_recommendation_without_appropriate_permissions(
    api_client, standard_case, final_advice_url, gov_headers
):
    response = api_client.post(final_advice_url, data={}, **gov_headers)
    assert response.status_code == 403
    assert response.json()["errors"] == {"detail": "You do not have permission to perform this action."}

    assert standard_case.advice.filter(level=AdviceLevel.FINAL).count() == 0


def test_user_cannot_edit_final_recommendation_without_appropriate_permissions(
    api_client, gov_user, standard_case, final_advice_url, gov_headers
):
    initial_data = {"text": "approve", "proviso": "condition"}
    good_on_application = standard_case.goods.first()
    final_advice = FinalAdviceFactory(
        user=gov_user,
        case=standard_case,
        good=good_on_application.good,
        **initial_data,
    )

    response = api_client.put(
        final_advice_url,
        data=[{"id": str(final_advice.id), "text": "updated_advice", "proviso": ""}],
        **gov_headers,
    )
    assert response.status_code == 403
    assert response.json()["errors"] == {"detail": "You do not have permission to perform this action."}

    assert [
        {
            "text": item.text,
            "proviso": item.proviso,
        }
        for item in standard_case.advice.filter(level=AdviceLevel.FINAL)
    ] == [initial_data]


def test_user_cannot_delete_final_recommendation_without_appropriate_permissions(
    api_client, gov_user, standard_case, final_advice_url, gov_headers
):
    good_on_application = standard_case.goods.first()
    FinalAdviceFactory(
        user=gov_user,
        case=standard_case,
        good=good_on_application.good,
    )

    response = api_client.delete(final_advice_url, **gov_headers)
    assert response.status_code == 403
    assert response.json()["errors"] == {"detail": "You do not have permission to perform this action."}
    assert standard_case.advice.filter(level=AdviceLevel.FINAL).count() == 1
