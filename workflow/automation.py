from cases.models import Case, CaseAssignment
from teams.models import Team
from workflow.routing_rules.models import RoutingRule
from workflow.user_queue_assignment import get_next_status_in_workflow_sequence


def run_routing_rules(case: Case):
    case.remove_all_case_assignments()
    rules_have_been_applied = False
    while not rules_have_been_applied:
        case_parameter_set = case.parameter_set()
        for team in Team.objects.all():
            team_rule_tier = None
            for rule in RoutingRule.objects.filter(team=team, status=case.status).order_by("tier"):
                if team_rule_tier and team_rule_tier != rule.tier:
                    break
                for parameter_set in rule.parameter_sets():
                    if parameter_set.issubset(case_parameter_set):
                        case.queues.add(rule.queue)
                        if rule.user:
                            CaseAssignment(user=rule.user, queue=rule.queue, case=case).save()
                        team_rule_tier = rule.tier
                        rules_have_been_applied = True
                        break

        if not rules_have_been_applied:
            next_status = get_next_status_in_workflow_sequence(case)
            if next_status:
                case.status = next_status
                case.save()
