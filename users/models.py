import uuid

import reversion
from django.contrib.auth.models import AbstractUser
from django.db import models

from organisations.models import Organisation
from users.managers import CustomUserManager


@reversion.register()
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(default=None, blank=True, unique=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    objects = CustomUserManager
