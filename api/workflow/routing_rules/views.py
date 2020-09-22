from django.http import JsonResponse
from rest_framework import exceptions
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK
from rest_framework.views import APIView

from api.core.authentication import GovAuthentication
from api.core.constants import GovPermissions
from lite_content.lite_api.strings import RoutingRules
from api.workflow.routing_rules.enum import StatusAction
from api.workflow.routing_rules.helpers import get_routing_rule
from api.workflow.routing_rules.models import RoutingRule
from api.workflow.routing_rules.serializers import RoutingRuleSerializer, SmallRoutingRuleSerializer


class RoutingRulesList(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = RoutingRuleSerializer
    queryset = RoutingRule.objects.all()

    def filter_queryset(self, queryset):
        filtered_qs = queryset
        filter_data = self.request.GET

        if not self.request.user.govuser.has_permission(GovPermissions.MANAGE_ALL_ROUTING_RULES):
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

    def initial(self, request, *args, **kwargs):
        if request.user.govuser.has_permission(GovPermissions.MANAGE_TEAM_ROUTING_RULES) or request.user.govuser.has_permission(
            GovPermissions.MANAGE_ALL_ROUTING_RULES
        ):
            return super(RoutingRulesList, self).initial(request, *args, **kwargs)
        else:
            raise exceptions.PermissionDenied()


class RoutingRulesDetail(RetrieveUpdateAPIView):
    authentication_classes = (GovAuthentication,)

    def initial(self, request, *args, **kwargs):
        if request.user.govuser.has_permission(GovPermissions.MANAGE_TEAM_ROUTING_RULES) or request.user.govuser.has_permission(
            GovPermissions.MANAGE_ALL_ROUTING_RULES
        ):
            return super(RoutingRulesDetail, self).initial(request, *args, **kwargs)
        else:
            raise exceptions.PermissionDenied()

    def get_serializer_class(self):
        if self.request.method == "GET":
            # light weight serializer for editing
            return SmallRoutingRuleSerializer
        else:
            # heavy serializer for validating, saving and getting list of objects
            return RoutingRuleSerializer

    def get_queryset(self):
        if self.request.user.govuser.has_permission(GovPermissions.MANAGE_ALL_ROUTING_RULES):
            return RoutingRule.objects.filter(id=self.kwargs["pk"])
        else:
            return RoutingRule.objects.filter(id=self.kwargs["pk"], team_id=self.request.user.govuser.team.id)

    def perform_update(self, serializer):
        # Don't update the data during validate_only requests
        if not self.request.data.get("validate_only", False):
            serializer.save()


class RoutingRulesActiveStatus(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        status = request.data.get("status")

        if status not in [StatusAction.DEACTIVATE, StatusAction.REACTIVATE]:
            raise ValueError(RoutingRules.Errors.BAD_STATUS)

        active_status = status == StatusAction.REACTIVATE

        routing_rule = get_routing_rule(id=pk)

        if routing_rule.active == active_status:
            return JsonResponse(status=HTTP_400_BAD_REQUEST, data={"error": RoutingRules.Errors.STATUS_ALREADY_SET})

        routing_rule.active = active_status
        routing_rule.save()

        return JsonResponse(
            status=HTTP_200_OK, data={"routing_rule": SmallRoutingRuleSerializer(instance=routing_rule).data}
        )
