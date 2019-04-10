from django.db import models
from organisations.models import Organisation
import uuid
import reversion


@reversion.register()
class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(default=None, blank=True)
    password = models.TextField(default=None, blank=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
