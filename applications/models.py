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


class FormComplete:
    def __init__(self, draft):
        self.ready_for_submission = True
        if draft.user_id == '':
            self.user_id = "user_id cannot be blank"
            self.ready_for_submission = False
        if draft.usage == '':
            self.usage = "usage cannot be blank"
            self.ready_for_submission = False
        if draft.activity == '':
            self.activity = "activity cannot be blank"
            self.ready_for_submission = False
        if draft.destination == '':
            self.destination = "destination cannot be blank"
            self.ready_for_submission = False
        if draft.control_code == '':
            self.control_code = "control_code cannot be blank"
            self.ready_for_submission = False
