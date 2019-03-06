from django.db import models
import uuid


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.TextField(default=None)
    control_code = models.TextField(default=None, blank=True)
    activity = models.TextField(default=None, blank=True)
    destination = models.TextField(default=None, blank=True)
    usage = models.TextField(default=None, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        db_table = "application"
