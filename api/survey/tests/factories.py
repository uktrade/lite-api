import factory

from faker import Faker

from django.utils import timezone


from api.cases.enums import CaseTypeEnum
from api.survey.enums import (
    HelpfulGuidanceEnum,
    RecommendationChoiceType,
    UserAccountEnum,
    ExperiencedIssueEnum,
    UserJourney,
)
from api.survey.models import SurveyResponse

faker = Faker()


class SurveyResponseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SurveyResponse

    case_type_id = CaseTypeEnum.SIEL.id
    feedback_submission_date = factory.LazyFunction(timezone.now)
    user_journey = factory.fuzzy.FuzzyChoice(UserJourney.choices, getter=lambda t: t[0])
    satisfaction_rating = factory.fuzzy.FuzzyChoice(RecommendationChoiceType.choices, getter=lambda t: t[0])
    experienced_issues = factory.List(
        [
            ExperiencedIssueEnum.NO_ISSUE,
            ExperiencedIssueEnum.OTHER,
        ]
    )
    guidance_application_process_helpful = factory.fuzzy.FuzzyChoice(HelpfulGuidanceEnum.choices, getter=lambda t: t[0])
    process_of_creating_account = factory.fuzzy.FuzzyChoice(UserAccountEnum.choices, getter=lambda t: t[0])
