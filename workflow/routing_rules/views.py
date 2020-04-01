from rest_framework.generics import ListCreateAPIView
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from workflow.routing_rules.serializers import RoutingRuleSerializer


class RoutingRulesList(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = RoutingRuleSerializer


class RoutingRulesDetail(APIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = RoutingRuleSerializer
