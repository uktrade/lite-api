import uuid

import reversion
from django.db import models
from reversion.models import Revision

from gov_users.enums import GovUserStatuses
from teams.models import Team


class Permission(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=30)
    name = models.CharField(default=None, blank=True, null=True, max_length=30)


@reversion.register()
class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(default=None, blank=True, null=True, max_length=30)
    permissions = models.ManyToManyField(Permission, related_name='roles')


@reversion.register()
class GovUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(choices=GovUserStatuses.choices, default=GovUserStatuses.ACTIVE, max_length=20)
    first_name = models.CharField(default=None, blank=True, null=True, max_length=30)
    last_name = models.CharField(default=None, blank=True, null=True, max_length=30)
    email = models.EmailField(default=None, blank=False, unique=True)
    team = models.ForeignKey(Team, related_name='team', on_delete=models.PROTECT)
    role = models.ForeignKey(Role, related_name='role', default='00000000-0000-0000-0000-000000000001', on_delete=models.PROTECT)

    def unassign_from_cases(self):
        """
        Remove user from all cases
        """
        self.case_assignments.clear()


class GovUserRevisionMeta(models.Model):
    revision = models.OneToOneField(Revision, on_delete=models.CASCADE)
    gov_user = models.ForeignKey(GovUser, on_delete=models.CASCADE)
