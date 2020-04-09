from django.http import Http404, JsonResponse
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.constants import GovPermissions
from conf.exceptions import PermissionDeniedError
from workflow.routing_rules.helpers import get_routing_rule
from workflow.routing_rules.models import RoutingRule
from workflow.routing_rules.serializers import RoutingRuleSerializer, SmallRoutingRuleSerializer


class RoutingRulesList(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = RoutingRuleSerializer
    queryset = RoutingRule.objects.all()

    def filter_queryset(self, queryset):
        filtered_qs = queryset
        # get each filter
        filter_data = self.request.GET

        if not self.request.user.has_permission(GovPermissions.MANAGE_ALL_ROUTING_RULES):
            filtered_qs = filtered_qs.filter(team_id=self.request.user.team.id)

        if filter_data.get("case_status"):
            filtered_qs = filtered_qs.filter(status_id=filter_data.get("case_status"))

        if filter_data.get("team"):
            filtered_qs = filtered_qs.filter(team_id=filter_data.get("team"))

        if filter_data.get("queue"):
            filtered_qs = filtered_qs.filter(queue_id=filter_data.get("queue"))

        if filter_data.get("tier"):
            filtered_qs = filtered_qs.filter(tier=filter_data.get("tier"))

        if filter_data.get("only_active"):
            filtered_qs = filtered_qs.filter(active=filter_data.get("only_active"))

        return filtered_qs

    def get(self, request, *args, **kwargs):
        if request.user.has_permission(GovPermissions.MANAGE_TEAM_ROUTING_RULES) or request.user.has_permission(
            GovPermissions.MANAGE_ALL_ROUTING_RULES
        ):
            return super().get(request, *args, **kwargs)
        else:
            raise PermissionDeniedError()

    def post(self, request, *args, **kwargs):
        if request.user.has_permission(GovPermissions.MANAGE_TEAM_ROUTING_RULES) or request.user.has_permission(
            GovPermissions.MANAGE_ALL_ROUTING_RULES
        ):
            return super().post(request, *args, **kwargs)
        else:
            raise PermissionDeniedError()


class RoutingRulesDetail(RetrieveUpdateAPIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, *args, **kwargs):
        if request.user.has_permission(GovPermissions.MANAGE_TEAM_ROUTING_RULES) or request.user.has_permission(
            GovPermissions.MANAGE_ALL_ROUTING_RULES
        ):
            return super().get(request, *args, **kwargs)
        else:
            raise PermissionDeniedError()

    def put(self, request, *args, **kwargs):
        if request.user.has_permission(GovPermissions.MANAGE_TEAM_ROUTING_RULES) or request.user.has_permission(
            GovPermissions.MANAGE_ALL_ROUTING_RULES
        ):
            return super().put(request, *args, **kwargs)
        else:
            raise PermissionDeniedError()

    def get_serializer_class(self):
        if self.request.method == "GET":
            # light weight serializer for editing
            return SmallRoutingRuleSerializer
        else:
            # heavy serializer for validating, saving and getting list of objects
            return RoutingRuleSerializer

    def get_queryset(self):
        return RoutingRule.objects.filter(id=self.kwargs["pk"])

    def perform_update(self, serializer):
        if not self.request.data.get("validate_only", False):
            serializer.save()


class RoutingRulesActiveStatus(APIView):
    def put(self, request, pk):
        status = request.data.get("status")

        if status != "deactivate" and status != "reactivate":
            raise Http404

        active_status = status == "reactivate"

        routing_rule = get_routing_rule(id=pk)

        if routing_rule.active == active_status:
            return JsonResponse(status=HTTP_400_BAD_REQUEST, data={"error": "status already set"})

        routing_rule.active = active_status
        routing_rule.save()

        return JsonResponse(
            status=HTTP_200_OK, data={"routing_rule": SmallRoutingRuleSerializer(instance=routing_rule).data}
        )
