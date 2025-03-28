import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q

from api.common.models import TimestampableModel
from api.flags.enums import FlagLevels, FlagStatuses, FlagColours, FlagPermissions
from api.teams.models import Team


class FlagQuerySet(models.QuerySet):
    def filter_by_applicable_team(self, team):
        return self.filter(Q(team=team) | Q(applicable_by_team=team))


class FlagManager(models.Manager):

    def get_queryset(self):
        return FlagQuerySet(self.model, using=self._db)

    def get_by_natural_key(self, name):
        return self.get(name=name)

    def filter_by_applicable_team(self, team):
        return self.get_queryset().filter_by_applicable_team(team)


class Flag(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(default="Untitled Flag", unique=True, max_length=100)
    alias = models.TextField(default=None, null=True, unique=True, help_text="fixed static field for reference")
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    level = models.CharField(choices=FlagLevels.choices, max_length=20)
    status = models.CharField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE, max_length=20)
    label = models.CharField(max_length=15, null=True, blank=True)
    colour = models.CharField(choices=FlagColours.choices, default=FlagColours.DEFAULT, max_length=20)
    priority = models.PositiveSmallIntegerField(default=0)
    blocks_finalising = models.BooleanField(default=False)
    removable_by = models.CharField(choices=FlagPermissions.choices, default=FlagPermissions.DEFAULT, max_length=50)
    applicable_by_team = models.ManyToManyField(to="teams.Team", related_name="applicable_flags")
    remove_on_finalised = models.BooleanField(default=False)

    objects = FlagManager()

    class Meta:
        db_table = "flag"
        ordering = ["team"]

    def natural_key(self):
        return (self.name,)


class FlaggingRuleManager(models.Manager):
    def get_by_natural_key(
        self,
        team_name,
        level,
        status,
        flag,
        matching_values,
        matching_groups,
        excluded_values,
        is_for_verified_goods_only,
    ):
        return self.get(
            team__name=team_name,
            level=level,
            status=status,
            flag__name=flag,
            matching_values=matching_values,
            matching_groups=matching_groups,
            excluded_values=excluded_values,
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
    is_python_criteria = models.BooleanField(default=False)
    description = models.TextField(default="", blank=True)

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
            self.matching_values,
            self.matching_groups,
            self.excluded_values,
            self.is_for_verified_goods_only,
        )
