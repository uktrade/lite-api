import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models

from api.common.models import TimestampableModel
from api.flags.enums import FlagLevels, FlagStatuses, FlagColours
from api.teams.models import Team


class FlagManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Flag(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(default="Untitled Flag", unique=True, max_length=25)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    level = models.CharField(choices=FlagLevels.choices, max_length=20)
    status = models.CharField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE, max_length=20)
    label = models.CharField(max_length=15, null=True, blank=True)
    colour = models.CharField(choices=FlagColours.choices, default=FlagColours.DEFAULT, max_length=20)
    priority = models.PositiveSmallIntegerField(default=0)
    blocks_approval = models.BooleanField(null=False, blank=False, default=False)

    objects = FlagManager()

    class Meta:
        db_table = "flag"
        ordering = ["team"]

    def natural_key(self):
        return (self.name,)


class FlaggingRuleManager(models.Manager):
    def get_by_natural_key(self, team_name, level, status, flag, matching_value, is_for_verified_goods_only):
        return self.get(
            team__name=team_name,
            level=level,
            status=status,
            flag__name=flag,
            matching_value=matching_value,
            is_for_verified_goods_only=is_for_verified_goods_only,
        )


class FlaggingRule(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    level = models.CharField(choices=FlagLevels.choices, max_length=20)
    status = models.CharField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE, max_length=20)
    flag = models.ForeignKey(Flag, on_delete=models.CASCADE, related_name="flagging_rules")
    matching_values = ArrayField(models.TextField(default=""), default=list)
    matching_groups = ArrayField(models.TextField(default=""), default=list)
    excluded_values = ArrayField(models.TextField(default=""), default=list)
    is_for_verified_goods_only = models.BooleanField(null=True, blank=True)

    objects = FlaggingRuleManager()

    class Meta:
        db_table = "flagging_rule"
        indexes = [models.Index(fields=["created_at"])]
        ordering = ["team__name", "-created_at"]

    def natural_key(self):
        return (
            self.team.name,
            self.level,
            self.status,
            self.flag.name,
            self.matching_value,
            self.is_for_verified_goods_only,
        )
