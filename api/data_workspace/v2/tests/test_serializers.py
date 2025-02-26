import pytest

from api.data_workspace.v2.serializers import GoodDescriptionSerializer
from api.staticdata.report_summaries.tests.factories import ReportSummaryFactory


pytestmark = pytest.mark.django_db


def test_good_description_just_subject_matches_model():
    just_subject = ReportSummaryFactory(
        prefix=None,
        subject__name="Just subject",
    )

    class MockGoodOnApplication:
        pass

    obj = MockGoodOnApplication()
    obj.report_summary_prefix_name = None
    obj.report_summary_subject_name = "Just subject"
    obj.id = 12345

    assert just_subject.name == GoodDescriptionSerializer(instance=obj).data["description"]


def test_good_description_prefix_and_subject_matches_model():
    prefix_and_subject = ReportSummaryFactory(
        prefix__name="prefix",
        subject__name="subject",
    )

    class MockGoodOnApplication:
        pass

    obj = MockGoodOnApplication()
    obj.report_summary_prefix_name = "prefix"
    obj.report_summary_subject_name = "subject"
    obj.id = 12345

    assert prefix_and_subject.name == GoodDescriptionSerializer(instance=obj).data["description"]
