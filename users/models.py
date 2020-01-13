import uuid
from abc import abstractmethod

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from common.models import TimestampableModel

from conf.constants import Roles
from static.statuses.models import CaseStatus
from teams.models import Team
from users.enums import UserStatuses, UserType
from users.managers import InternalManager, ExporterManager


class Permission(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=30)
    name = models.CharField(default="permission - FIX", max_length=80)
    # For convenience using UserType as a proxy for Permission Type
    type = models.CharField(choices=UserType.choices, default=UserType.INTERNAL, max_length=30)

    objects = models.Manager()
    exporter = ExporterManager()
    internal = InternalManager()

    class Meta:
        ordering = ["name"]


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(default=None, blank=True, null=True, max_length=30)
    permissions = models.ManyToManyField(Permission, related_name="roles")
    type = models.CharField(choices=UserType.choices, default=UserType.INTERNAL, max_length=30)
    organisation = models.ForeignKey("organisations.Organisation", on_delete=models.CASCADE, null=True)
    statuses = models.ManyToManyField(CaseStatus, related_name="roles")


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


class BaseUser(AbstractUser, TimestampableModel):
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


class BaseNotification(models.Model):
    user = models.ForeignKey(BaseUser, on_delete=models.CASCADE, null=False)

    # All notifications are currently linked to a case
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, null=False)

    # Generic Foriegn Key Fields
    content_type = models.ForeignKey(ContentType, default=None, on_delete=models.CASCADE)
    object_id = models.UUIDField(default=uuid.uuid4)
    content_object = GenericForeignKey("content_type", "object_id")


class ExporterNotification(BaseNotification):
    organisation = models.ForeignKey("organisations.Organisation", on_delete=models.CASCADE, null=False)


class GovNotification(BaseNotification):
    pass


class ExporterUser(BaseUser):
    def send_notification(self, organisation, content_object, case):
        ExporterNotification.objects.create(
            user=self, organisation=organisation, content_object=content_object, case=case
        )

    def get_role(self, organisation):
        return self.userorganisationrelationship_set.get(organisation=organisation).role

    def set_role(self, organisation, role):
        uor = self.userorganisationrelationship_set.get(organisation=organisation)
        uor.role = role
        uor.save()

    def has_permission(self, permission, organisation):
        user_permissions = self.get_role(organisation).permissions.values_list("id", flat=True)
        return permission.name in user_permissions


class GovUser(BaseUser):
    status = models.CharField(choices=UserStatuses.choices, default=UserStatuses.ACTIVE, max_length=20)
    team = models.ForeignKey(Team, related_name="team", on_delete=models.PROTECT)
    role = models.ForeignKey(
        Role, related_name="role", default=Roles.INTERNAL_DEFAULT_ROLE_ID, on_delete=models.PROTECT
    )

    def unassign_from_cases(self):
        """
        Remove gov user from all cases
        """
        self.case_assignments.clear()

    def send_notification(self, content_object, case):
        from audit_trail.models import Audit

        if isinstance(content_object, Audit):
            # There can only be one notification per gov user's case
            # If a notification for that gov user's case already exists, update the case activity it points to
            try:
                content_type = ContentType.objects.get_for_model(Audit)
                notification = GovNotification.objects.get(user=self, content_type=content_type, case=case)
                notification.content_object = content_object
                notification.save()
            except GovNotification.DoesNotExist:
                GovNotification.objects.create(user=self, content_object=content_object, case=case)

    def has_permission(self, permission):
        user_permissions = self.role.permissions.values_list("id", flat=True)
        return permission.name in user_permissions


class UserOrganisationRelationship(TimestampableModel):
    user = models.ForeignKey(ExporterUser, on_delete=models.CASCADE)
    organisation = models.ForeignKey("organisations.Organisation", on_delete=models.CASCADE)
    role = models.ForeignKey(
        Role, related_name="exporter_role", default=Roles.EXPORTER_DEFAULT_ROLE_ID, on_delete=models.PROTECT
    )
    status = models.CharField(choices=UserStatuses.choices, default=UserStatuses.ACTIVE, max_length=20)

    def send_notification(self, content_object, case):
        self.user.send_notification(organisation=self.organisation, content_object=content_object, case=case)
