import uuid
from django.db import models

from api.common.models import TimestampableModel
from api.survey.enums import HelpfulGuidanceChoiceType, RecommendationChoiceType, UserAccountChoiceType


# Create your models here.
class SurveyResponse(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    recommendation = models.TextField(
        choices=RecommendationChoiceType.choices,
    )
    other_detail = models.TextField(blank=True, null=True)
    experienced_issue = models.JSONField(blank=True, null=True)
    helpful_guidance = models.TextField(choices=HelpfulGuidanceChoiceType.choices, blank=True, default="")
    user_account_process = models.TextField(choices=UserAccountChoiceType.choices, blank=True, default="")
    service_improvements_feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return "SurveyResponse #{0} - {1}".format(self.id, self.recommendation)
