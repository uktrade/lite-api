import uuid

import reversion
from django.db import models
from reversion.models import Revision

from teams.models import Team


class Permission(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=30)
    name = models.CharField(default=None, blank=True, null=True, max_length=30)


@reversion.register()
class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(default=None, blank=True, null=True, max_length=30)
    permissions = models.ManyToManyField(Permission, related_name='roles')
