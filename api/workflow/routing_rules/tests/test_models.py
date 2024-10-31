from django.conf import settings
from parameterized import parameterized

from api.cases.models import CaseType, CaseStatus
from api.cases.tests.factories import CaseFactory
from api.flags.models import Flag, FlaggingRule
from api.workflow.routing_rules.models import RoutingRule, RoutingHistory
from api.queues.models import Queue
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.models import BaseUser
from api.users.enums import SystemUser
from test_helpers.clients import DataTestClient


class RoutingHistoryCreationTests(DataTestClient):
    @parameterized.expand(
        [
            ["routing_engine", "flag", "add"],
            ["routing_engine", "queue", "add"],
            ["manual", "flag", "remove"],
            ["manual", "queue", "remove"],
        ]
    )
    def test_create_routing_history_record(self, orchestrator_type, entity_type, action):
        initial_checks = CaseStatus.objects.get(status=CaseStatusEnum.INITIAL_CHECKS)
        case = CaseFactory(
            status=initial_checks,
            case_type=CaseType.objects.get(reference="siel"),
        )
        if orchestrator_type == "routing_engine":
            orchestrator = BaseUser.objects.get(id=SystemUser.id)
        else:
            orchestrator = BaseUser.objects.first()
        flag = Flag.objects.first()
        case.flags.add(flag)
        queue = Queue.objects.first()
        case.queues.add(queue)
        if entity_type == "flag":
            entity = flag
            rule_id = FlaggingRule.objects.first().id
        else:
            entity = queue
            rule_id = RoutingRule.objects.first().id

        result = RoutingHistory.create(
            case=case,
            entity=entity,
            action=action,
            orchestrator_type=orchestrator_type,
            orchestrator=orchestrator,
            rule_identifier=rule_id,
        )

        routing_history = RoutingHistory.objects.get(id=result.id)
        assert routing_history.id == result.id
        assert routing_history.case == case
        assert routing_history.entity == entity
        assert routing_history.action == action
        assert routing_history.orchestrator_type == orchestrator_type
        assert routing_history.case_status == case.status
        assert routing_history.case_flags == [str(flag.id) for flag in case.flags.all()]
        assert routing_history.case_queues == [str(queue.id) for queue in case.queues.all()]
        assert routing_history.rule_identifier == str(rule_id)
        assert routing_history.commit_sha == settings.GIT_COMMIT_SHA
