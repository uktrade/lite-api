from django.http import Http404, JsonResponse
from rest_framework.generics import ListCreateAPIView
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from workflow.routing_rules.models import RoutingRule
from workflow.routing_rules.serializers import RoutingRuleSerializer


class RoutingRulesList(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = RoutingRuleSerializer
    queryset = RoutingRule.objects.all()


class RoutingRulesDetail(APIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = RoutingRuleSerializer


class RoutingRulesActiveStatus(APIView):
    def put(self, request, pk, status):

        if status != "deactivate" and status != "reactivate":
            raise Http404

        active_status = True if status == "reactivate" else False

        routing_rule = RoutingRule.objects.get(id=pk)

        if routing_rule.active == active_status:
            return JsonResponse(status=HTTP_400_BAD_REQUEST, data={"error": "status already set"})

        routing_rule.active = active_status
        routing_rule.save()

        return JsonResponse(
            status=HTTP_200_OK, data={"routing_rule": RoutingRuleSerializer(instance=routing_rule).data}
        )
