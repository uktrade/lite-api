import pytest

from django.urls import reverse
from django.utils import timezone
from pytest_bdd import (
    given,
    then,
    when,
    scenarios,
)
from unittest import mock

from api.cases.enums import AdviceType, LicenceDecisionType
from api.cases.models import LicenceDecision
from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from api.staticdata.statuses.enums import CaseStatusEnum


scenarios("../scenarios/licence_decisions.feature")


@pytest.fixture()
def licence_decisions_list_url():
    return reverse("data_workspace:v2:dw-licence-decisions-list")


@when("I fetch all licence decisions", target_fixture="licence_decisions")
def fetch_licence_decisions(licence_decisions_list_url, unpage_data):
    return unpage_data(licence_decisions_list_url)


@given("a standard draft licence is created", target_fixture="draft_licence")
def standard_draft_licence_created(standard_draft_licence):
    assert standard_draft_licence.status == LicenceStatus.DRAFT
    return standard_draft_licence


@then("the draft licence is not included in the extract")
def draft_licence_not_included_in_extract(draft_licence, unpage_data, licence_decisions_list_url):
    licences = unpage_data(licence_decisions_list_url)

    assert str(draft_licence.case.id) not in [item["application_id"] for item in licences]


@given("a standard licence is cancelled", target_fixture="cancelled_licence")
def standard_licence_is_cancelled(standard_licence):
    standard_licence.status = LicenceStatus.CANCELLED
    standard_licence.save()

    return standard_licence


@then("the cancelled licence is not included in the extract")
def cancelled_licence_not_included_in_extract(cancelled_licence, unpage_data, licence_decisions_list_url):
    licences = unpage_data(licence_decisions_list_url)

    assert str(cancelled_licence.case.id) not in [item["application_id"] for item in licences]


@then("I see issued licence is included in the extract")
def licence_included_in_extract(issued_licence, unpage_data, licence_decisions_list_url):
    licences = unpage_data(licence_decisions_list_url)

    assert str(issued_licence.case.id) in [item["application_id"] for item in licences]


@then("I see refused case is included in the extract")
def refused_case_included_in_extract(refused_case, unpage_data, licence_decisions_list_url):
    licences = unpage_data(licence_decisions_list_url)

    assert str(refused_case.id) in [item["application_id"] for item in licences]


@given("a case is ready to be finalised", target_fixture="case_with_final_advice")
def case_ready_to_be_finalised(standard_case_with_final_advice):
    assert standard_case_with_final_advice.status.status == CaseStatusEnum.UNDER_FINAL_REVIEW
    return standard_case_with_final_advice


@given("a case is ready to be refused", target_fixture="case_with_refused_advice")
def case_ready_to_be_refused(standard_case_with_refused_advice):
    assert standard_case_with_refused_advice.status.status == CaseStatusEnum.UNDER_FINAL_REVIEW
    return standard_case_with_refused_advice


@when("the licence for the case is approved")
def licence_for_case_is_approved(client, gov_headers, case_with_final_advice):
    data = {"action": AdviceType.APPROVE, "duration": 24}
    for good_on_app in case_with_final_advice.goods.all():
        data[f"quantity-{good_on_app.id}"] = str(good_on_app.quantity)
        data[f"value-{good_on_app.id}"] = str(good_on_app.value)

    issue_date = timezone.now()
    data.update({"year": issue_date.year, "month": issue_date.month, "day": issue_date.day})

    url = reverse("applications:finalise", kwargs={"pk": case_with_final_advice.id})
    response = client.put(url, data, content_type="application/json", **gov_headers)
    assert response.status_code == 200
    response = response.json()

    assert response["reference_code"] is not None
    licence = Licence.objects.get(reference_code=response["reference_code"])
    assert licence.status == LicenceStatus.DRAFT


@when("case officer generates licence documents")
def case_officer_generates_licence_documents(client, siel_template, gov_headers, case_with_final_advice):
    data = {
        "template": str(siel_template.id),
        "text": "",
        "visible_to_exporter": False,
        "advice_type": AdviceType.APPROVE,
    }
    url = reverse(
        "cases:generated_documents:generated_documents",
        kwargs={"pk": str(case_with_final_advice.pk)},
    )
    with mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file", return_value=None):
        response = client.post(url, data, content_type="application/json", **gov_headers)
        assert response.status_code == 201


@when("case officer issues licence for this case", target_fixture="issued_licence")
def case_officer_issues_licence(client, gov_headers, case_with_final_advice):
    url = reverse(
        "cases:finalise",
        kwargs={"pk": str(case_with_final_advice.pk)},
    )
    response = client.put(url, {}, content_type="application/json", **gov_headers)
    assert response.status_code == 201

    case_with_final_advice.refresh_from_db()
    assert case_with_final_advice.status.status == CaseStatusEnum.FINALISED
    assert case_with_final_advice.sub_status.name == "Approved"

    response = response.json()
    assert response["licence"] is not None

    licence = Licence.objects.get(id=response["licence"])
    assert licence.status == LicenceStatus.ISSUED

    assert LicenceDecision.objects.filter(
        case=case_with_final_advice,
        decision=LicenceDecisionType.ISSUED,
    ).exists()

    return licence


@when("the licence for the case is refused")
def licence_for_case_is_refused(client, gov_headers, case_with_refused_advice):
    data = {"action": AdviceType.REFUSE}

    url = reverse("applications:finalise", kwargs={"pk": case_with_refused_advice.id})
    response = client.put(url, data, content_type="application/json", **gov_headers)
    assert response.status_code == 200


@when("case officer generates refusal documents")
def generate_refusal_documents(client, siel_refusal_template, gov_headers, case_with_refused_advice):
    data = {
        "template": str(siel_refusal_template.id),
        "text": "",
        "visible_to_exporter": False,
        "advice_type": AdviceType.REFUSE,
    }
    url = reverse(
        "cases:generated_documents:generated_documents",
        kwargs={"pk": str(case_with_refused_advice.pk)},
    )
    with mock.patch("api.cases.generated_documents.views.s3_operations.upload_bytes_file", return_value=None):
        response = client.post(url, data, content_type="application/json", **gov_headers)
        assert response.status_code == 201


@when("case officer refuses licence for this case", target_fixture="refused_case")
def licence_for_case_is_refused(client, gov_headers, case_with_refused_advice):
    url = reverse(
        "cases:finalise",
        kwargs={"pk": str(case_with_refused_advice.pk)},
    )
    response = client.put(url, {}, content_type="application/json", **gov_headers)
    assert response.status_code == 201

    case_with_refused_advice.refresh_from_db()
    assert case_with_refused_advice.status.status == CaseStatusEnum.FINALISED
    assert case_with_refused_advice.sub_status.name == "Refused"

    assert LicenceDecision.objects.filter(
        case=case_with_refused_advice,
        decision=LicenceDecisionType.REFUSED,
    ).exists()

    return case_with_refused_advice


@when("case officer revokes issued licence", target_fixture="revoked_licence")
def case_officer_revokes_licence(client, lu_sr_manager_headers, issued_licence):
    url = reverse("licences:licence_details", kwargs={"pk": str(issued_licence.pk)})
    response = client.patch(
        url, {"status": LicenceStatus.REVOKED}, content_type="application/json", **lu_sr_manager_headers
    )
    assert response.status_code == 200

    assert LicenceDecision.objects.filter(
        case=issued_licence.case,
        decision=LicenceDecisionType.REVOKED,
    ).exists()

    revoked_licence = LicenceDecision.objects.get(
        case=issued_licence.case, decision=LicenceDecisionType.REVOKED
    ).licence

    return revoked_licence


@then("I see revoked licence is included in the extract")
def revoked_licence_decision_included_in_extract(licence_decisions, revoked_licence):

    all_revoked_licences = [item for item in licence_decisions if item["decision"] == "revoked"]

    assert str(revoked_licence.case.id) in [item["application_id"] for item in all_revoked_licences]