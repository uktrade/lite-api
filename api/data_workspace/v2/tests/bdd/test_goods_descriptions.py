from pytest_bdd import (
    given,
    parsers,
    scenarios,
    when,
)

from django.urls import reverse

from api.applications.tests.factories import GoodOnApplicationFactory
from api.staticdata.report_summaries.models import (
    ReportSummaryPrefix,
    ReportSummarySubject,
)


scenarios("./scenarios/goods_descriptions.feature")


@given(parsers.parse("the application has the following goods:{goods}"))
def given_the_application_has_the_following_goods(parse_table, draft_standard_application, goods):
    draft_standard_application.goods.all().delete()
    good_attributes = parse_table(goods)[1:]
    for id, name in good_attributes:
        GoodOnApplicationFactory(
            application=draft_standard_application,
            id=id,
            good__name=name,
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
