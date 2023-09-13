import uuid
from abc import abstractmethod
from phonenumber_field.modelfields import PhoneNumberField

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from api.common.models import TimestampableModel
from api.core.constants import Roles
from api.queues.constants import ALL_CASES_QUEUE_ID
from api.staticdata.statuses.models import CaseStatus
from api.teams.models import Team
from api.users.enums import UserStatuses, UserType
from api.users.managers import InternalManager, ExporterManager


class Permission(models.Model):
    id = models.TextField(primary_key=True, editable=False, max_length=100)
    name = models.TextField(default="permission - FIX", max_length=100)
    # For convenience using UserType as a proxy for Permission Type
    type = models.CharField(choices=UserType.non_system_choices(), default=UserType.INTERNAL, max_length=8)

    objects = models.Manager()
    exporter = ExporterManager()
    internal = InternalManager()

    class Meta:
        ordering = ["name"]


class RoleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("permissions")


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(default="", blank=True, max_length=100)
    permissions = models.ManyToManyField(Permission, related_name="roles")
    type = models.CharField(choices=UserType.non_system_choices(), default=UserType.INTERNAL, max_length=8)
    organisation = models.ForeignKey("organisations.Organisation", on_delete=models.CASCADE, null=True)
    statuses = models.ManyToManyField(CaseStatus, related_name="roles_statuses")

    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name}, type={self.type})"

    class Meta:
        ordering = ["name"]

    objects = RoleManager()


class CustomUserManager(BaseUserManager):
    """Cannot remove class as it's embedded in users/migrations/0001_initial"""

    use_in_migrations = False


class BaseUser(AbstractUser, TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(default=None, blank=True)
    password = None
    last_login = None
    type = models.CharField(choices=UserType.choices(), null=False, blank=False, max_length=8)
    phone_number = PhoneNumberField(default="")
    pending = models.BooleanField(default=True)

    @property
    def has_django_admin_permission(self):
        return self.email in settings.ALLOWED_ADMIN_EMAILS

    is_superuser = has_django_admin_permission
    is_staff = has_django_admin_permission
    is_active = True

    # Set this to use id as email cannot be unique in the base user model
    # (and we couldn't think of anything else to use instead)
    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["first_name", "last_name", "created_at"]
        unique_together = [["email", "type"]]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = self.email.lower() if self.email else None
        super().save(*args, **kwargs)

    @abstractmethod
    def send_notification(self, **kwargs):
        pass


class BaseNotification(models.Model):
    user = models.ForeignKey(BaseUser, on_delete=models.CASCADE, null=False)

    # All notifications are currently linked to a case
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, null=False)

    # Generic Foreign Key Fields (case notes, ecju queries, generated documents)
    content_type = models.ForeignKey(ContentType, default=None, on_delete=models.CASCADE)
    object_id = models.UUIDField(default=uuid.uuid4)
    content_object = GenericForeignKey("content_type", "object_id")


class ExporterNotification(BaseNotification):
    organisation = models.ForeignKey("organisations.Organisation", on_delete=models.CASCADE, null=False)


class GovNotification(BaseNotification):
    pass


class BaseUserCompatMixin:

    baseuser_ptr: BaseUser

    @property
    def username(self):
        return self.baseuser_ptr.username

    @property
    def first_name(self):
        return self.baseuser_ptr.first_name

    @property
    def last_name(self):
        return self.baseuser_ptr.last_name

    @property
    def email(self):
        return self.baseuser_ptr.email

    @property
    def phone_number(self):
        return self.baseuser_ptr.phone_number

    @property
    def is_anonymous(self):
        return self.baseuser_ptr.is_anonymous

    @property
    def pending(self):
        return self.baseuser_ptr.pending

    def save(self, *args, **kwargs):
        if not self.baseuser_ptr.type:
            self.baseuser_ptr.type = self.type
            self.baseuser_ptr.save()
        super().save(*args, **kwargs)


class ExporterUser(models.Model, BaseUserCompatMixin):

    baseuser_ptr = models.OneToOneField(
        BaseUser,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    type = UserType.EXPORTER
    external_id = models.CharField(max_length=200, default="", blank=True)

    def send_notification(self, organisation, content_object, case):
        ExporterNotification.objects.create(
            user=self.baseuser_ptr, organisation=organisation, content_object=content_object, case=case
        )

    def get_role(self, organisation_id):
        return self.relationship.get(organisation_id=organisation_id).role

    def set_role(self, organisation, role):
        uor = self.relationship.get(organisation=organisation)
        uor.role = role
        uor.save()

    def has_permission(self, permission, organisation):
        user_permissions = self.get_role(organisation).permissions.values_list("id", flat=True)
        return permission.name in user_permissions

    def is_in_organisation(self, organisation):
        return self.relationship.filter(organisation=organisation).exists()


class GovUser(models.Model, BaseUserCompatMixin):

    baseuser_ptr = models.OneToOneField(
        BaseUser,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    status = models.CharField(choices=UserStatuses.choices, default=UserStatuses.ACTIVE, max_length=20)
    team = models.ForeignKey(Team, related_name="users", on_delete=models.PROTECT)
    role = models.ForeignKey(
        Role, related_name="role", default=Roles.INTERNAL_DEFAULT_ROLE_ID, on_delete=models.PROTECT
    )
    default_queue = models.UUIDField(default=uuid.UUID(ALL_CASES_QUEUE_ID), null=False)
    type = UserType.INTERNAL

    def unassign_from_cases(self):
        """
        Remove gov user from all cases
        """
        self.case_assignments.filter(user=self).delete()

    def send_notification(self, content_object, case):
        from api.audit_trail.models import Audit

        if isinstance(content_object, Audit):
            # There can only be one notification per gov user's case
            # If a notification for that gov user's case already exists, update the case activity it points to
            try:
                content_type = ContentType.objects.get_for_model(Audit)
                notification = GovNotification.objects.get(user=self.baseuser_ptr, content_type=content_type, case=case)
                notification.content_object = content_object
                notification.save()
            except GovNotification.DoesNotExist:
                GovNotification.objects.create(user=self.baseuser_ptr, content_object=content_object, case=case)

    def has_permission(self, permission):
        user_permissions = self.role.permissions.values_list("id", flat=True)
        return permission.name in user_permissions


class UserOrganisationRelationship(TimestampableModel):
    user = models.ForeignKey(ExporterUser, on_delete=models.CASCADE)
    organisation = models.ForeignKey("organisations.Organisation", on_delete=models.CASCADE, related_name="users")
    role = models.ForeignKey(
        Role, related_name="exporter_role", default=Roles.EXPORTER_EXPORTER_ROLE_ID, on_delete=models.PROTECT
    )
    status = models.CharField(choices=UserStatuses.choices, default=UserStatuses.ACTIVE, max_length=20)

    def send_notification(self, content_object, case):
        self.user.send_notification(organisation=self.organisation, content_object=content_object, case=case)

    class Meta:
        default_related_name = "relationship"
