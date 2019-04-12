import uuid

import reversion
from django.contrib.auth.models import AbstractUser
from django.db import models

from organisations.models import Organisation


@reversion.register()
class User(AbstractUser):
    USERNAME_FIELD = 'email'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(default=None, blank=True, unique=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
