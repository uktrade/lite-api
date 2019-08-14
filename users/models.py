import uuid

import reversion
from reversion.models import Revision
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from organisations.models import Organisation
from teams.models import Team
from users.enums import UserStatuses


class Permission(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=30)
    name = models.CharField(default=None, blank=True, null=True, max_length=30)


@reversion.register()
class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(default=None, blank=True, null=True, max_length=30)
    permissions = models.ManyToManyField(Permission, related_name='roles')


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


@reversion.register()
class BaseUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(default=None, blank=True)
    status = models.CharField(choices=UserStatuses.choices, default=UserStatuses.ACTIVE, max_length=20)

    # Set this to use id as email cannot be unique in the base user model (and we couldn't think of anything else to use instead)
    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    objects = CustomUserManager()


class ExporterUser(BaseUser):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, default=None, null=True)

    def send_notification(self, case):
        from cases.models import Notification
        Notification.objects.create(user=self, note=case)


class GovUser(BaseUser):
    team = models.ForeignKey(Team, related_name='team', on_delete=models.PROTECT)
    role = models.ForeignKey(Role, related_name='role', default='00000000-0000-0000-0000-000000000001', on_delete=models.PROTECT)

    def unassign_from_cases(self):
        """
        Remove gov user from all cases
        """
        self.case_assignments.clear()


class GovUserRevisionMeta(models.Model):
    revision = models.OneToOneField(Revision, on_delete=models.CASCADE)
    gov_user = models.ForeignKey(GovUser, on_delete=models.CASCADE)


class UserOrganisationRelationship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(ExporterUser, related_name='organisation_assignments', on_delete=models.CASCADE,
                             blank=False, null=False)
    organisation = models.ForeignKey(Organisation, related_name='organisation_assignments', on_delete=models.CASCADE,
                                     blank=False, null=False)
    status = models.BooleanField(blank=False, null=False, default=True)