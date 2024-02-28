import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from api.common.models import TimestampableModel
from api.survey.enums import (
    HelpfulGuidanceEnum,
    RecommendationChoiceType,
    UserAccountEnum,
    ExperiencedIssueEnum,
    UserJourney,
)


# Create your models here.
class SurveyResponse(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    recommendation = models.CharField(
        choices=RecommendationChoiceType.choices,
    )
    other_detail = models.TextField(blank=True, default="")
    experienced_issue = ArrayField(models.CharField(choices=ExperiencedIssueEnum.choices), blank=True, null=True)
    helpful_guidance = models.CharField(choices=HelpfulGuidanceEnum.choices, blank=True, default="")
    user_account_process = models.CharField(choices=UserAccountEnum.choices, blank=True, default="")
    service_improvements_feedback = models.TextField(blank=True, default="")
    user_journey = models.CharField(choices=UserJourney.choices, blank=True, default="")

    def __str__(self):
        return f"SurveyResponse #{self.id} - {self.recommendation}"
