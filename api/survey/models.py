import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from model_utils.fields import AutoCreatedField

from api.cases.models import CaseType
from api.survey.enums import (
    HelpfulGuidanceEnum,
    RecommendationChoiceType,
    UserAccountEnum,
    ExperiencedIssueEnum,
    UserJourney,
)


# Create your models here.
class SurveyResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    feedback_submission_date = AutoCreatedField(_("feedback_submission_date"))
    case_type = models.ForeignKey(CaseType, on_delete=models.DO_NOTHING, blank=True, default=None)
    url = models.TextField(blank=True, default="N/A")
    user_journey = models.CharField(choices=UserJourney.choices, blank=True, default="")
    satisfaction_rating = models.CharField(
        choices=RecommendationChoiceType.choices,
    )
    experienced_issues = ArrayField(models.CharField(choices=ExperiencedIssueEnum.choices), blank=True, null=True)
    other_detail = models.TextField(blank=True, default="")
    service_improvements_feedback = models.TextField(blank=True, default="")
    guidance_application_process_helpful = models.CharField(choices=HelpfulGuidanceEnum.choices, blank=True, default="")
    process_of_creating_account = models.CharField(choices=UserAccountEnum.choices, blank=True, default="")

    def __str__(self):
        return f"SurveyResponse #{self.id} - {self.satisfaction_rating}"
