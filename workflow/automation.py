from cases.models import Case, CaseAssignment
from teams.models import Team
from workflow.routing_rules.models import RoutingRule


def run_routing_rules(case: Case):
    case.queues.clear()
    CaseAssignment.objects.filter(case=case).delete()
    case_parameter_set = case.parameter_set()
    for team in Team.objects.all():
        team_rule_tier = None
        for rule in RoutingRule.objects.filter(team=team).order_by("tier"):
            if team_rule_tier and team_rule_tier != rule.tier:
                break
            for parameter_set in rule.parameter_sets():
                if parameter_set.issubset(case_parameter_set):
                    case.queues.add(rule.queue)
                    if rule.user:
                        CaseAssignment(user=rule.user, queue=rule.queue, case=case).save()
                    team_rule_tier = rule.tier
                    break
