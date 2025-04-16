import pytest
from uuid import uuid4
from unittest import mock

from django.urls import reverse
from rest_framework.exceptions import ErrorDetail

from api.cases.models import LicenceDecision
from api.cases.generated_documents.tests.factories import GeneratedCaseDocumentFactory
from api.letter_templates.models import LetterTemplate
from api.f680.tests.factories import (
    F680RecipientFactory,
    F680SecurityReleaseRequestFactory,
    F680SecurityReleaseOutcomeFactory,
    SubmittedF680ApplicationFactory,
)
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.countries.factories import CountryFactory
from api.users.libraries.user_to_token import user_to_token

from lite_routing.routing_rules_internal.enums import TeamIdEnum


pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


@pytest.fixture(scope="function")
def setup(
    hawk_authentication,
):
    return


@pytest.fixture
def hawk_authentication(settings):
    settings.HAWK_AUTHENTICATION_ENABLED = True


@pytest.fixture
def url():
    def _finalise_url(f680_application):
        return reverse("cases:finalise", kwargs={"pk": f680_application.id})

    return _finalise_url


@pytest.fixture
def get_f680_application(organisation):

    def _get_f680_application():
        under_final_review = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        application = SubmittedF680ApplicationFactory(organisation=organisation, status=under_final_review)
        recipients = [
            F680RecipientFactory(
                country=CountryFactory(**{"id": "AU", "name": "Australia"}), organisation=organisation
            ),
            F680RecipientFactory(
                country=CountryFactory(**{"id": "NZ", "name": "New Zealand"}), organisation=organisation
            ),
        ]

        for recipient in recipients:
            F680SecurityReleaseRequestFactory(id=uuid4(), application=application, recipient=recipient)

        return application

    return _get_f680_application


@pytest.fixture
def get_f680_application_with_approve_outcome(get_f680_application):

    def _get_f680_application_with_approve_outcome():
        f680_application = get_f680_application()
        outcome = F680SecurityReleaseOutcomeFactory(
            case=f680_application.case_ptr,
            outcome="approve",
            security_grading="secret",
        )
        outcome.security_release_requests.set(f680_application.security_release_requests.all())
        return f680_application

    return _get_f680_application_with_approve_outcome


@pytest.fixture
def get_f680_application_with_refuse_outcome(get_f680_application):

    def _get_f680_application_with_refuse_outcome():
        f680_application = get_f680_application()
        outcome = F680SecurityReleaseOutcomeFactory(
            case=f680_application.case_ptr,
            outcome="refuse",
            refusal_reasons="nope",
        )
        outcome.security_release_requests.set(f680_application.security_release_requests.all())
        return f680_application

    return _get_f680_application_with_refuse_outcome


@pytest.fixture
def get_f680_application_with_mixed_outcome(get_f680_application):

    def _get_f680_application_with_mixed_outcome():
        f680_application = get_f680_application()
        refuse_outcome = F680SecurityReleaseOutcomeFactory(
            case=f680_application.case_ptr,
            outcome="refuse",
            refusal_reasons="nope",
        )
        refuse_outcome.security_release_requests.add(f680_application.security_release_requests.all()[0])
        approve_outcome = F680SecurityReleaseOutcomeFactory(
            case=f680_application.case_ptr,
            outcome="approve",
            security_grading="secret",
        )
        approve_outcome.security_release_requests.add(f680_application.security_release_requests.all()[1])
        return f680_application

    return _get_f680_application_with_mixed_outcome


# SIEL tests are located in api/cases/tests/test_finalise_advice.py
# TODO: Move SIEL tests over to this file and harmonise test cases
class TestFinaliseView:

    @mock.patch("api.cases.notify.notify_exporter_licence_issued")
    def test_finalise_f680_approve_success(
        self,
        mock_notify,
        get_hawk_client,
        url,
        get_f680_application_with_approve_outcome,
        team_case_advisor,
        team_case_advisor_headers,
    ):
        f680_application = get_f680_application_with_approve_outcome()
        case = f680_application.case_ptr
        f680_approve_letter_template = LetterTemplate.objects.get(name="F680 Approval")
        generated_document = GeneratedCaseDocumentFactory(
            template=f680_approve_letter_template, advice_type="approve", case=f680_application.case_ptr
        )

        gov_user = team_case_advisor(TeamIdEnum.MOD_ECJU)
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        api_client, target_url = get_hawk_client("PUT", url(f680_application))
        response = api_client.put(target_url, **headers)
        assert response.status_code == 201
        assert response.json() == {"case": str(f680_application.id), "licence": ""}
        f680_application.refresh_from_db()
        assert f680_application.status.status == CaseStatusEnum.FINALISED
        assert f680_application.sub_status.name == "Approved"
        assert LicenceDecision.objects.all().count() == 0
        mock_notify.assert_called_with(case)

    @mock.patch("api.cases.notify.notify_exporter_licence_refused")
    def test_finalise_f680_refuse_success(
        self,
        mock_notify,
        get_hawk_client,
        url,
        get_f680_application_with_refuse_outcome,
        team_case_advisor,
        team_case_advisor_headers,
    ):
        f680_application = get_f680_application_with_refuse_outcome()
        case = f680_application.case_ptr
        f680_refuse_letter_template = LetterTemplate.objects.get(name="F680 Refusal")
        generated_document = GeneratedCaseDocumentFactory(
            template=f680_refuse_letter_template, advice_type="refuse", case=f680_application.case_ptr
        )

        gov_user = team_case_advisor(TeamIdEnum.MOD_ECJU)
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        api_client, target_url = get_hawk_client("PUT", url(f680_application))
        response = api_client.put(target_url, **headers)
        assert response.status_code == 201
        assert response.json() == {"case": str(f680_application.id), "licence": ""}
        f680_application.refresh_from_db()
        assert f680_application.status.status == CaseStatusEnum.FINALISED
        assert f680_application.sub_status.name == "Refused"
        assert LicenceDecision.objects.all().count() == 0
        mock_notify.assert_called_with(case)

    @mock.patch("api.cases.notify.notify_exporter_licence_refused")
    def test_finalise_f680_mixed_outcome_success(
        self,
        mock_notify,
        get_hawk_client,
        url,
        get_f680_application_with_mixed_outcome,
        team_case_advisor,
        team_case_advisor_headers,
    ):
        f680_application = get_f680_application_with_mixed_outcome()
        case = f680_application.case_ptr
        f680_refuse_letter_template = LetterTemplate.objects.get(name="F680 Refusal")
        generated_document = GeneratedCaseDocumentFactory(
            template=f680_refuse_letter_template, advice_type="refuse", case=f680_application.case_ptr
        )
        f680_approve_letter_template = LetterTemplate.objects.get(name="F680 Approval")
        generated_document = GeneratedCaseDocumentFactory(
            template=f680_approve_letter_template, advice_type="approve", case=f680_application.case_ptr
        )

        gov_user = team_case_advisor(TeamIdEnum.MOD_ECJU)
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        api_client, target_url = get_hawk_client("PUT", url(f680_application))
        response = api_client.put(target_url, **headers)
        assert response.status_code == 201
        assert response.json() == {"case": str(f680_application.id), "licence": ""}
        f680_application.refresh_from_db()
        assert f680_application.status.status == CaseStatusEnum.FINALISED
        # TODO: Should a case with a mixed outcome have sub status approved?
        assert f680_application.sub_status.name == "Approved"
        assert LicenceDecision.objects.all().count() == 0
        mock_notify.assert_called_with(case)

    def test_finalise_f680_missing_letters(
        self,
        get_hawk_client,
        url,
        get_f680_application_with_approve_outcome,
        team_case_advisor,
        team_case_advisor_headers,
    ):
        f680_application = get_f680_application_with_approve_outcome()

        gov_user = team_case_advisor(TeamIdEnum.MOD_ECJU)
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        api_client, target_url = get_hawk_client("PUT", url(f680_application))
        response = api_client.put(target_url, **headers)
        assert response.status_code == 400
        assert response.data == {
            "errors": {
                "decision-approve": [
                    ErrorDetail(string="No decision document generated", code="parse_error"),
                ],
            },
        }
        f680_application.refresh_from_db()
        assert f680_application.status.status == CaseStatusEnum.UNDER_FINAL_REVIEW

    def test_finalise_f680_wrong_case_status_permission_denied(
        self,
        get_hawk_client,
        url,
        get_f680_application_with_approve_outcome,
        team_case_advisor,
        team_case_advisor_headers,
    ):
        f680_application = get_f680_application_with_approve_outcome()
        ogd_advice = CaseStatus.objects.get(status=CaseStatusEnum.OGD_ADVICE)
        f680_application.status = ogd_advice
        f680_application.save()

        gov_user = team_case_advisor(TeamIdEnum.MOD_ECJU)
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        api_client, target_url = get_hawk_client("PUT", url(f680_application))
        response = api_client.put(target_url, **headers)
        assert response.status_code == 403
        f680_application.refresh_from_db()
        assert f680_application.status.status == CaseStatusEnum.OGD_ADVICE

    def test_finalise_f680_wrong_team_permission_denied(
        self,
        get_hawk_client,
        url,
        get_f680_application_with_approve_outcome,
        team_case_advisor,
        team_case_advisor_headers,
    ):
        f680_application = get_f680_application_with_approve_outcome()

        gov_user = team_case_advisor(TeamIdEnum.MOD_CAPPROT)
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        api_client, target_url = get_hawk_client("PUT", url(f680_application))
        response = api_client.put(target_url, **headers)
        assert response.status_code == 403
        f680_application.refresh_from_db()
        assert f680_application.status.status == CaseStatusEnum.UNDER_FINAL_REVIEW
