from django.db import models
from enumchoicefield import ChoiceEnum, EnumChoiceField
import uuid
import reversion

from organisations.models import Organisation


class ApplicationStatuses(ChoiceEnum):
    submitted = "Submitted"
    more_information_required = "More information required"
    under_review = "Under review"
    resubmitted = "Resubmitted"
    withdrawn = "Withdrawn"
    approved = "Approved"
    declined = "Declined"


@reversion.register()
class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True, null=True)
    activity = models.TextField(default=None, blank=True, null=True)
    destination = models.TextField(default=None, blank=True, null=True)
    usage = models.TextField(default=None, blank=True, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True)
    status = EnumChoiceField(enum_class=ApplicationStatuses, default=ApplicationStatuses.submitted)
