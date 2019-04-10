from django.db import models
import uuid
import reversion


@reversion.register()
class Application(models.Model):
    APPLICATION_STATUSES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("More information required", "More information required"),
        ("Under review", "Under review"),
        ("Resubmitted", "Resubmitted"),
        ("Withdrawn", "Withdrawn")
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.TextField(default=None)
    name = models.TextField(default=None, blank=True, null=True)
    control_code = models.TextField(default=None, blank=True, null=True)
    activity = models.TextField(default=None, blank=True, null=True)
    destination = models.TextField(default=None, blank=True, null=True)
    usage = models.TextField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True)
    status = models.TextField(default="Submitted", choices=APPLICATION_STATUSES)


@reversion.register()
class Good(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    description = models.TextField(default=None, blank=True)
    quantity = models.IntegerField()
    control_code = models.TextField(default=None, blank=True)
    application = models.ForeignKey(Application, related_name='goods', on_delete=models.CASCADE)


@reversion.register()
class Destination(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    application = models.ForeignKey(Application, related_name='destinations', on_delete=models.CASCADE)
