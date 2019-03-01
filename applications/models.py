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
        if draft.user_id == None:
            self.user_id = "User id cannot be blank"
            self.ready_for_submission = False
        if draft.usage == None:
            self.usage = "Usage cannot be blank"
            self.ready_for_submission = False
        if draft.activity == None:
            self.activity = "Activity cannot be blank"
            self.ready_for_submission = False
        if draft.destination == None:
            self.destination = "Destination cannot be blank"
            self.ready_for_submission = False
        if draft.control_code == None:
            self.control_code = "Control code cannot be blank"
            self.ready_for_submission = False
