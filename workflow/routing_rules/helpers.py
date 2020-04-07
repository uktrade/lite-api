from conf.exceptions import NotFoundError
from workflow.routing_rules.models import RoutingRule


def get_routing_rule(id):
    try:
        return RoutingRule.objects.get(id=id)
    except RoutingRule.DoesNotExist:
        raise NotFoundError({"RoutingRule": "routing rule not found"})
