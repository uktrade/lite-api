from django.db import models
import uuid


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.TextField(default=None)
    name = models.TextField(default=None, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True)


class Good(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    quantity = models.IntegerField()
    control_code = models.TextField(default=None, blank=True)
    application = models.ForeignKey(Application, related_name='goods', on_delete=models.CASCADE)


class Destination(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    application = models.ForeignKey(Application, related_name='destinations', on_delete=models.CASCADE)
