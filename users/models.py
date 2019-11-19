import uuid
from abc import abstractmethod

import reversion
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from conf.constants import Roles
from organisations.models import Organisation
from queries.models import Query
from teams.models import Team
from users.enums import UserStatuses, UserType


class Permission(models.Model):
    class Meta:
        unique_together = (('id', 'type'),)

    id = models.CharField(primary_key=True, editable=False, max_length=30)
    name = models.CharField(default=None, blank=True, null=True, max_length=30)
    type = models.CharField(choices=UserType.choices, default=UserType.INTERNAL, max_length=30)


@reversion.register()
class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(default=None, blank=True, null=True, max_length=30)
    permissions = models.ManyToManyField(Permission, related_name="roles")
    type = models.CharField(choices=UserType.choices, default=UserType.INTERNAL, null=True, max_length=30)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, null=True)


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email, and password.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


@reversion.register()
class BaseUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(default=None, blank=True)
    password = None
    is_superuser = None
    last_login = None
    is_staff = None
    is_active = None

    # Set this to use id as email cannot be unique in the base user model
    # (and we couldn't think of anything else to use instead)
    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    objects = CustomUserManager()

    @abstractmethod
    def send_notification(self, **kwargs):
        pass


class ExporterUser(BaseUser):
    def send_notification(self, case_note=None, query=None, ecju_query=None):
        from cases.models import Notification

        # circular import prevention

        if case_note:
            Notification.objects.create(user=self, case_note=case_note)
        elif query:
            actual_query = Query.objects.get(id=query.id)
            Notification.objects.create(user=self, query=actual_query)
        elif ecju_query:
            Notification.objects.create(user=self, ecju_query=ecju_query)
        else:
            raise Exception("ExporterUser.send_notification: objects expected have not been added.")

    def get_role(self, organisation):
        return self.userorganisationrelationship_set.get(organisation=organisation).role

    def set_role(self, organisation, role):
        uor = self.userorganisationrelationship_set.get(organisation=organisation)
        uor.role = role
        uor.save()


class UserOrganisationRelationship(models.Model):
    user = models.ForeignKey(ExporterUser, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    role = models.ForeignKey(
        Role,
        related_name="exporter_role",
        default=Roles.EXPORTER_DEFAULT_ROLE_ID,
        on_delete=models.PROTECT,
    )
    status = models.CharField(choices=UserStatuses.choices, default=UserStatuses.ACTIVE, max_length=20)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)


class GovUser(BaseUser):
    status = models.CharField(choices=UserStatuses.choices, default=UserStatuses.ACTIVE, max_length=20)
    team = models.ForeignKey(Team, related_name="team", on_delete=models.PROTECT)
    role = models.ForeignKey(Role, related_name="role", default=Roles.DEFAULT_ROLE_ID, on_delete=models.PROTECT,)

    status = models.CharField(
        choices=UserStatuses.choices, default=UserStatuses.ACTIVE, max_length=20
    )
    team = models.ForeignKey(Team, related_name="team", on_delete=models.PROTECT)

    def unassign_from_cases(self):
        """
        Remove gov user from all cases
        """
        self.case_assignments.clear()

    # pylint: disable=W0221
    def send_notification(self, case_activity=None):
        from cases.models import Notification

        # circular import prevention

        if case_activity:
            # There can only be one notification per gov user's case
            # If a notification for that gov user's case already exists, update the case activity it points to
            try:
                notification = Notification.objects.get(user=self, case_activity__case=case_activity.case)
                notification.case_activity = case_activity
                notification.save()
            except Notification.DoesNotExist:
                Notification.objects.create(user=self, case_activity=case_activity)
        else:
            raise Exception("GovUser.send_notification: objects expected have not been added.")

    # Adds the first user as a super user
    # pylint: disable=W0221
    # pylint: disable=E1003
    def save(self, *args, **kwargs):
        if GovUser.objects.filter(role_id=Roles.INTERNAL_SUPER_USER_ROLE_ID).count() == 0:
            self.role_id = Roles.INTERNAL_SUPER_USER_ROLE_ID
        super(BaseUser, self).save(*args, **kwargs)
