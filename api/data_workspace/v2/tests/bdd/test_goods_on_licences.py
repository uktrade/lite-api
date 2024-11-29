from django.urls import reverse
from pytest_bdd import given, parsers, scenarios, when

from api.applications.tests.factories import GoodOnApplicationFactory
from api.licences.tests.factories import StandardLicenceFactory
from api.licences.enums import LicenceStatus
from api.staticdata.report_summaries.models import (
    ReportSummaryPrefix,
    ReportSummarySubject,
)

scenarios("./scenarios/goods_on_licences.feature")


@given(parsers.parse("a standard application with the following goods:{goods}"), target_fixture="standard_application")
def standard_application_with_following_goods(parse_table, goods, standard_application):
    standard_application.goods.all().delete()
    good_attributes = parse_table(goods)[1:]
    for id, name in good_attributes:
        GoodOnApplicationFactory(
            application=standard_application,
            id=id,
            good__name=name,
        )
    return standard_application


@given(parsers.parse("a draft licence with attributes:{attributes}"), target_fixture="draft_licence")
def draft_licence_with_attributes(parse_attributes, attributes, standard_application):
    draft_licence = StandardLicenceFactory(
        case=standard_application, status=LicenceStatus.DRAFT, **parse_attributes(attributes)
    )
    return draft_licence


@when("the licence is issued")
def licence_is_issued(standard_application, issue_licence):
    issue_licence(standard_application)
    standard_application.refresh_from_db()
    return standard_application


@given(parsers.parse("the goods are assessed by TAU as:{assessments}"))
def the_goods_are_assessed_by_tau_as(
    parse_table,
    standard_application,
    assessments,
    api_client,
    lu_case_officer,
    gov_headers,
):
    assessments = parse_table(assessments)[1:]
    url = reverse("assessments:make_assessments", kwargs={"case_pk": standard_application.pk})

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
    parsers.parse("a draft standard application with the following goods:{goods}"), target_fixture="draft_application"
)
def draft_standard_application_with_following_goods(parse_table, goods, draft_application):
    draft_application.goods.all().delete()
    good_attributes = parse_table(goods)[1:]
    for id, name in good_attributes:
        GoodOnApplicationFactory(
            application=draft_application,
            id=id,
            good__name=name,
        )
    return draft_application
