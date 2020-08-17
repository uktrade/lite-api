from api.core.exceptions import NotFoundError
from lite_content.lite_api.strings import RoutingRules
from api.workflow.routing_rules.models import RoutingRule


def get_routing_rule(id):
    try:
        return RoutingRule.objects.get(id=id)
    except RoutingRule.DoesNotExist:
        raise NotFoundError({"RoutingRule": RoutingRules.Errors.NOT_FOUND})
