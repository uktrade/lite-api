from django.db import models
from enumchoicefield import ChoiceEnum, EnumChoiceField
import uuid
import reversion

from goods.models import Good


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
    user_id = models.TextField(default=None)
    name = models.TextField(default=None, blank=True, null=True)
    activity = models.TextField(default=None, blank=True, null=True)
    destination = models.TextField(default=None, blank=True, null=True)
    usage = models.TextField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True)
    status = EnumChoiceField(enum_class=ApplicationStatuses, default=ApplicationStatuses.submitted)


@reversion.register()
class GoodOnApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    good = models.ForeignKey(Good, related_name='goods', on_delete=models.CASCADE)
    application = models.ForeignKey(Application, related_name='goods', on_delete=models.CASCADE)
    quantity = models.FloatField(null=True, blank=True, default=None)
    unit = models.TextField(default=None)
    end_use_case = models.TextField(default=None)
    value = models.DecimalField(max_digits=256, decimal_places=2)


@reversion.register()
class Destination(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    application = models.ForeignKey(Application, related_name='destinations', on_delete=models.CASCADE)
