from api.audit_trail.enums import AuditType
from cases.models import Case, CaseAssignment
from api.staticdata.statuses.enums import CaseStatusEnum
from api.teams.models import Team
from api.users.enums import SystemUser, UserStatuses
from api.users.models import BaseUser
from api.workflow.routing_rules.models import RoutingRule
from api.workflow.user_queue_assignment import get_next_status_in_workflow_sequence
from api.audit_trail import service as audit_trail_service


def run_routing_rules(case: Case, keep_status: bool = False):
    """
    Will run active routing rules against the case team by team, for its current status and any subsequent status
    until any rules are run.

    :param case: Case object the rules are run against
    :param keep_status: boolean field to determine if rules should be ran against next status, if no rules run for
        current status
    """
    # remove all current queue and user assignments to the case
    case.remove_all_case_assignments()
    rules_have_been_applied = False
    case_parameter_set = case.parameter_set()

    system_user = BaseUser.objects.get(id=SystemUser.id)

    while not rules_have_been_applied:
        # look at each team one at a time
        for team in Team.objects.all():
            team_rule_tier = None

            # get each active routing rule for the given team, at the current status of the case,
            #   ordered by tier ascending
            for rule in (
                RoutingRule.objects.select_related("queue", "user")
                .filter(team=team, status=case.status, active=True)
                .order_by("tier")
            ):
                # If a rule has been run, the tier is set, and we wish to set all routing rules of that tier that make
                #   sense, so only break once routing rules tier changes
                if team_rule_tier and team_rule_tier != rule.tier:
                    break

                for parameter_set in rule.parameter_sets():
                    # If the rule set is a subset of the case's set we wish to assign the user and queue to the case,
                    #   and set the team rule tier for the future.
                    if parameter_set.issubset(case_parameter_set):
                        case.queues.add(rule.queue)
                        audit_trail_service.create(
                            actor=system_user,
                            verb=AuditType.MOVE_CASE,
                            action_object=case.get_case(),
                            payload={"queues": rule.queue.name},
                        )
                        # Only assign active users to the case
                        if rule.user and rule.user.status == UserStatuses.ACTIVE:
                            # Two rules of the same user, queue, and case assignment may exist with
                            # difference conditions, we should ensure these do not overlap
                            if not CaseAssignment.objects.filter(user=rule.user, queue=rule.queue, case=case).exists():
                                CaseAssignment(user=rule.user, queue=rule.queue, case=case).save(audit_user=system_user)
                        team_rule_tier = rule.tier
                        rules_have_been_applied = True
                        break

        # If no rules have been applied, we wish to either move to the next status, or break loop if keep_status is True
        #   or the next status is terminal
        if not rules_have_been_applied:
            next_status = get_next_status_in_workflow_sequence(case)
            if next_status and not next_status.is_terminal and not keep_status:
                old_status = case.status
                case.status = next_status
                case.save()
                audit_trail_service.create(
                    actor=system_user,
                    verb=AuditType.UPDATED_STATUS,
                    target=case,
                    payload={
                        "status": {
                            "new": CaseStatusEnum.get_text(next_status.status),
                            "old": CaseStatusEnum.get_text(old_status.status),
                        }
                    },
                )
            else:
                rules_have_been_applied = True
