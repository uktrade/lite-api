import uuid

from django.db import models
from django.db.models import Q

from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import queryable_property

from api.staticdata.statuses.enums import CaseStatusEnum


class CaseStatusManager(QueryablePropertiesManager):
    def get_by_natural_key(self, status):
        return self.get(status=status)


class CaseStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=50, unique=True)
    priority = models.PositiveSmallIntegerField(null=False, blank=False)
    workflow_sequence = models.PositiveSmallIntegerField(null=True)
    next_workflow_status = models.ForeignKey("CaseStatus", on_delete=models.DO_NOTHING, null=True, blank=True)

    objects = CaseStatusManager()

    @queryable_property
    def is_terminal(self):
        return CaseStatusEnum.is_terminal(self.status)

    @is_terminal.filter(boolean=True)
    @classmethod
    def is_terminal(cls):
        return Q(status__in=CaseStatusEnum.terminal_statuses())

    @queryable_property
    def is_read_only(self):
        return CaseStatusEnum.is_read_only(self.status)

    @is_read_only.filter(boolean=True)
    @classmethod
    def is_read_only(cls):
        return Q(status__in=CaseStatusEnum.read_only_statuses())

    @property
    def is_major_editable(self):
        return CaseStatusEnum.is_major_editable_status(self.status)

    @property
    def can_invoke_major_editable(self):
        return CaseStatusEnum.can_invoke_major_edit(self.status)

    @property
    def is_caseworker_operable(self):
        return CaseStatusEnum.is_caseworker_operable(self.status)

    def natural_key(self):
        return (self.status,)

    def __str__(self):
        return self.status


class CaseSubStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    parent_status = models.ForeignKey(CaseStatus, on_delete=models.CASCADE, related_name="sub_statuses")
    order = models.PositiveSmallIntegerField(default=100)


class CaseStatusCaseType(models.Model):
    class Meta:
        unique_together = ("case_type", "status")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_type = models.ForeignKey("cases.CaseType", on_delete=models.DO_NOTHING, null=True, blank=False, default=None)
    status = models.ForeignKey(CaseStatus, on_delete=models.CASCADE, null=False)
