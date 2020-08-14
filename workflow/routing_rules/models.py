import uuid

from django.db import models
from separatedvaluesfield.models import SeparatedValuesField

from cases.models import CaseType
from api.common.models import TimestampableModel
from flags.enums import FlagStatuses
from flags.models import Flag
from queues.models import Queue
from static.countries.models import Country
from static.statuses.models import CaseStatus
from teams.models import Team
from users.models import GovUser
from workflow.routing_rules.enum import RoutingRulesAdditionalFields


class RoutingRule(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, related_name="routing_rules", on_delete=models.CASCADE)
    queue = models.ForeignKey(Queue, related_name="routing_rules", on_delete=models.DO_NOTHING,)
    status = models.ForeignKey(CaseStatus, related_name="routing_rules", on_delete=models.DO_NOTHING,)
    tier = models.PositiveSmallIntegerField()  # positive whole number, that decides order routing rules are applied
    additional_rules = SeparatedValuesField(
        choices=RoutingRulesAdditionalFields.choices, max_length=100, blank=True, null=True, default=None
    )
    active = models.BooleanField(default=True)

    # optional fields that are required depending on values in additional_rules
    user = models.ForeignKey(GovUser, related_name="routing_rules", on_delete=models.DO_NOTHING, blank=True, null=True)
    case_types = models.ManyToManyField(CaseType, related_name="routing_rules", blank=True)
    flags = models.ManyToManyField(Flag, related_name="routing_rules", blank=True)
    country = models.ForeignKey(
        Country, related_name="routing_rules", on_delete=models.DO_NOTHING, blank=True, null=True
    )

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
        if self.flags.exclude(status=FlagStatuses.ACTIVE).exists():
            return parameter_sets

        if self.country:
            country_set = {self.country}
        else:
            country_set = set()

        flag_and_country_set = set(self.flags.all()) | country_set

        for case_type in self.case_types.all():
            parameter_set = flag_and_country_set | {case_type}
            parameter_sets.append(parameter_set)

        if not parameter_sets:
            parameter_sets = [flag_and_country_set]

        return parameter_sets
