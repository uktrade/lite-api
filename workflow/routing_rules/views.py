from django.http import Http404, JsonResponse
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from workflow.routing_rules.models import RoutingRule
from workflow.routing_rules.serializers import RoutingRuleSerializer, EditRoutingRuleSerializer


class RoutingRulesList(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = RoutingRuleSerializer
    queryset = RoutingRule.objects.all()


class RoutingRulesDetail(RetrieveUpdateAPIView):
    authentication_classes = (GovAuthentication,)

    def get_serializer_class(self):
        if self.request.method == "GET":
            # light weight serializer for editing
            return EditRoutingRuleSerializer
        else:
            # heavy serializer for validating, saving and getting list of objects
            return RoutingRuleSerializer

    def get_object(self):
        return RoutingRule.objects.get(id=self.kwargs["pk"])

    def perform_update(self, serializer):
        if not self.request.data.get("validate_only", False):
            serializer.save()


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
