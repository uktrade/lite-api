from django.db import models
import uuid


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.TextField(default='')

    class Meta:
        db_table = "application"

class FormComplete:
    def __init__(self, draft):
        self.ready_for_submission = True
        if draft.usage == '':
            self.usage = "Usage cannot be blank"
            self.ready_for_submission = False
        if draft.activity == '':
            self.activity = "Activity cannot be blank"
            self.ready_for_submission = False
        if draft.destination == '':
            self.destination = "Destination cannot be blank"
            self.ready_for_submission = False
        if draft.control_code == '':
            self.control_code = "Control code cannot be blank"
            self.ready_for_submission = False
