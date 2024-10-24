import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from separatedvaluesfield.models import SeparatedValuesField

from api.cases.models import CaseType
from api.common.models import TimestampableModel
from api.flags.enums import FlagStatuses
from api.flags.models import Flag
from api.queues.models import Queue
from api.staticdata.countries.models import Country
from api.staticdata.statuses.models import CaseStatus
from api.teams.models import Team
from api.users.models import GovUser
from api.workflow.routing_rules.enum import RoutingRulesAdditionalFields
from lite_routing.routing_rules_internal.routing_rules_criteria import run_criteria_function


class RoutingRuleManager(models.Manager):
    def get_by_natural_key(self, team_name, queue_name, status, tier, additional_rules, active, country_code):
        return self.get(
            team__name=team_name,
            queue__name=queue_name,
            status=status,
            tier=tier,
            additional_rules=additional_rules,
            active=active,
            country_id=country_code,
        )


class RoutingRule(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, related_name="routing_rules", on_delete=models.CASCADE)
    queue = models.ForeignKey(
        Queue,
        related_name="routing_rules",
        on_delete=models.DO_NOTHING,
    )
    status = models.ForeignKey(
        CaseStatus,
        related_name="routing_rules",
        on_delete=models.DO_NOTHING,
    )
    tier = models.PositiveSmallIntegerField()  # positive whole number, that decides order routing rules are applied
    additional_rules = SeparatedValuesField(
        choices=RoutingRulesAdditionalFields.choices, max_length=100, blank=True, null=True, default=None
    )
    active = models.BooleanField(default=True)

    # optional fields that are required depending on values in additional_rules
    user = models.ForeignKey(GovUser, related_name="routing_rules", on_delete=models.DO_NOTHING, blank=True, null=True)
    case_types = models.ManyToManyField(CaseType, related_name="routing_rules", blank=True)
    flags_to_include = models.ManyToManyField(Flag, related_name="routing_rules", blank=True)
    flags_to_exclude = models.ManyToManyField(Flag, related_name="exclude_routing_rules", blank=True)
    country = models.ForeignKey(
        Country, related_name="routing_rules", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    is_python_criteria = models.BooleanField(default=False)
    description = models.TextField(default="", blank=True)

    objects = RoutingRuleManager()

    class Meta:
        indexes = [models.Index(fields=["created_at", "tier"])]
        ordering = ["team__name", "tier", "-created_at"]

    def parameter_sets(self):
        """
        Generate a list of sets, containing all the possible subsets of the rule which are true to the condition
            of routing rules. We generate one set for each case_type as we can not have multiple case_types in the set
            (would cause all rules to fail)
        :return: list of sets
        """

        parameter_sets = []

        # Exclude the rule by returning and empty list if there are any inactive flags in the rule
        if (
            self.flags_to_include.exclude(status=FlagStatuses.ACTIVE).exists()
            or self.flags_to_exclude.exclude(status=FlagStatuses.ACTIVE).exists()
        ):
            return parameter_sets

        country_set = {self.country} if self.country else set()

        flag_and_country_set = set(self.flags_to_include.all()) | country_set

        for case_type in self.case_types.all():
            parameter_set = {"flags_country_set": flag_and_country_set | {case_type}}
            if self.flags_to_exclude:
                parameter_set["flags_to_exclude"] = set(self.flags_to_exclude.all())

            parameter_sets.append(parameter_set)

        if not parameter_sets:
            parameter_sets = [
                {"flags_country_set": flag_and_country_set, "flags_to_exclude": set(self.flags_to_exclude.all())},
            ]

        return parameter_sets

    def natural_key(self):
        return (
            self.team.name,
            self.queue.name,
            self.status,
            self.tier,
            self.additional_rules,
            self.active,
            self.country_id,  # country code
        )

    def is_python_criteria_satisfied(self, case):
        if not self.is_python_criteria:
            raise NotImplementedError(f"is_python_criteria_satisfied was run for non-python rule {self.id}")
        return run_criteria_function(self.id, case)

    natural_key.dependencies = ["teams.Team", "queues.Queue", "users.GovUser", "countries.Country"]


class RoutingHistory(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, related_name="routing_history_records")
    # used to limit the models that can be referred to by `entity` generic foreign key - only Flag and Queue
    _entity_limit = models.Q(app_label="queues", model="Queue") | models.Q(app_label="flags", model="Flag")
    entity_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        db_index=True,
        null=True,
        blank=True,
        limit_choices_to=_entity_limit,
        related_name="+",
    )
    entity_object_id = models.CharField(max_length=255, db_index=True)
    entity = GenericForeignKey("entity_content_type", "entity_object_id")
    action = models.CharField(max_length=10, choices=[("add", "Add"), ("remove", "Remove")])
    orchestrator_type = models.CharField(
        max_length=20, choices=[("manual", "Manual"), ("routing_engine", "Routing Engine")]
    )
    orchestrator = models.ForeignKey("users.BaseUser", on_delete=models.PROTECT, related_name="+")
    case_status = models.ForeignKey(
        CaseStatus,
        on_delete=models.PROTECT,
        related_name="+",
    )
    case_flags = models.JSONField()
    case_queues = models.JSONField()
    rule_identifier = models.CharField(max_length=256, default="", blank=True)
    commit_sha = models.CharField(max_length=40)

    @classmethod
    def create(cls, case, entity, action, orchestrator_type, orchestrator, rule_identifier):
        case_flags = [str(flag.id) for flag in case.flags.all()]
        case_queues = [str(queue.id) for queue in case.queues.all()]
        routing_history = RoutingHistory.objects.create(
            case=case,
            entity=entity,
            action=action,
            orchestrator_type=orchestrator_type,
            orchestrator=orchestrator,
            case_status=case.status,
            case_flags=case_flags,
            case_queues=case_queues,
            rule_identifier=rule_identifier,
            commit_sha=settings.GIT_COMMIT_SHA,
        )
        return routing_history
