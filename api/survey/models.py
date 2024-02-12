import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from api.common.models import TimestampableModel
from api.survey.enums import SatisfactionRatingEnum, RecommendationChoiceType, UserAccountEnum, ExperiencedIssueEnum


# Create your models here.
class SurveyResponse(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    recommendation = models.CharField(
        choices=RecommendationChoiceType.choices,
    )
    other_detail = models.TextField(blank=True, default="")
    experienced_issue = ArrayField(models.CharField(choices=ExperiencedIssueEnum.choices), blank=True, null=True)
    helpful_guidance = models.CharField(choices=SatisfactionRatingEnum.choices, blank=True, default="")
    user_account_process = models.CharField(choices=UserAccountEnum.choices, blank=True, default="")
    service_improvements_feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return "SurveyResponse #{0} - {1}".format(self.id, self.recommendation)
