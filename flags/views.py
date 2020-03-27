from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.models import GoodOnApplication, CountryOnApplication, StandardApplication, HmrcQuery
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.models import Case
from conf.authentication import GovAuthentication
from conf.constants import GovPermissions
from conf.helpers import str_to_bool
from conf.permissions import assert_user_has_permission
from flags.enums import FlagStatuses
from flags.helpers import get_object_of_level
from flags.libraries.get_flag import get_flag, get_flagging_rule
from flags.models import Flag, FlaggingRule
from flags.serializers import FlagSerializer, FlagAssignmentSerializer, FlaggingRuleSerializer
from goods.models import Good
from lite_content.lite_api import strings
from parties.models import Party
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queries.goods_query.models import GoodsQuery
from static.countries.models import Country
from workflow.flagging_rules_automation import apply_flagging_rule_to_all_open_cases, apply_flagging_rule_for_flag


@permission_classes((permissions.AllowAny,))
class FlagsList(APIView):
    """
    List all flags and perform actions on the list
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Returns list of all flags
        """
        level = request.GET.get("level")  # Case, Good
        team = request.GET.get("team")  # True, False
        include_deactivated = request.GET.get("include_deactivated")  # will be True/False

        flags = Flag.objects.all()

        if level:
            flags = flags.filter(level=level)

        if team:
            flags = flags.filter(team=request.user.team.id)

        if not str_to_bool(include_deactivated, invert_none=True):
            flags = flags.exclude(status=FlagStatuses.DEACTIVATED)

        flags = flags.order_by("name")
        serializer = FlagSerializer(flags, many=True)
        return JsonResponse(data={"flags": serializer.data})

    def post(self, request):
        """
        Add a new flag
        """
        data = JSONParser().parse(request)
        data["team"] = request.user.team.id
        serializer = FlagSerializer(data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"flag": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class FlagDetail(APIView):
    """
    Details of a specific flag
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Returns details of a specific flag
        """
        flag = get_flag(pk)
        serializer = FlagSerializer(flag)
        return JsonResponse(data={"flag": serializer.data})

    def put(self, request, pk):
        """
        Edit details of a specific flag
        """
        flag = get_flag(pk)

        # Prevent a user changing a flag if it does not belong to their team
        if request.user.team != flag.team:
            return JsonResponse(data={"errors": strings.Flags.FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

        serializer = FlagSerializer(instance=flag, data=request.data, partial=True)

        if serializer.is_valid():
            flag = serializer.save()
            apply_flagging_rule_for_flag(flag)
            return JsonResponse(data={"flag": serializer.data})

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class AssignFlags(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request):
        """
        Assigns flags to goods and cases
        """
        data = JSONParser().parse(request)
        level = data.get("level")[:-1].lower()
        response_data = []
        # If the data provided isn't in a list format, append it to a list
        objects = data.get("objects")
        if not isinstance(objects, list):
            objects = [objects]

        # Loop through all objects provided and append flags to them
        for pk in objects:
            obj = get_object_of_level(level, pk)
            serializer = FlagAssignmentSerializer(
                data=data, context={"team": request.user.team, "level": level.title()}
            )

            if serializer.is_valid():
                self._assign_flags(
                    flags=serializer.validated_data.get("flags"),
                    level=level.title(),
                    note=serializer.validated_data.get("note"),
                    obj=obj,
                    user=request.user,
                )
                response_data.append({level.lower(): serializer.data})
            else:
                return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data=response_data, status=status.HTTP_200_OK, safe=False)

    def _assign_flags(self, flags, level, note, obj, user):
        level = level.title()
        previously_assigned_team_flags = obj.flags.filter(level=level, team=user.team)
        previously_assigned_deactivated_team_flags = obj.flags.filter(
            level=level, team=user.team, status=FlagStatuses.DEACTIVATED
        )
        previously_assigned_not_team_flags = obj.flags.exclude(level=level, team=user.team)

        added_flags = [flag.name for flag in flags if flag not in previously_assigned_team_flags]
        ignored_flags = flags + [x for x in previously_assigned_deactivated_team_flags]
        removed_flags = [flag.name for flag in previously_assigned_team_flags if flag not in ignored_flags]

        # Add activity item

        if isinstance(obj, Case):
            self._set_case_activity(added_flags, removed_flags, obj, user, note)

        if isinstance(obj, Good):
            cases = []

            cases.extend(Case.objects.filter(id__in=GoodsQuery.objects.filter(good=obj).values_list("id", flat=True)))

            cases.extend(
                Case.objects.filter(id__in=GoodOnApplication.objects.filter(good=obj).values_list("id", flat=True))
            )

            for case in cases:
                self._set_case_activity_for_goods(added_flags, removed_flags, case, user, note, good=obj)

        if isinstance(obj, Party):
            case = self._get_case_for_destination(obj)
            self._set_case_activity_for_destinations(added_flags, removed_flags, case, user, note, destination=obj)

        if isinstance(obj, Country):
            cases = Case.objects.filter(
                id__in=CountryOnApplication.objects.filter(country=obj.id).values_list("application", flat=True)
            )

            for case in cases:
                self._set_case_activity_for_destinations(added_flags, removed_flags, case, user, note, destination=obj)

        obj.flags.set(
            flags + list(previously_assigned_not_team_flags) + list(previously_assigned_deactivated_team_flags)
        )

    def _set_case_activity(self, added_flags, removed_flags, case, user, note, **kwargs):
        # Add an activity item for the case
        if added_flags:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.ADD_FLAGS,
                target=case,
                payload={"added_flags": added_flags, "additional_text": note,},
            )

        if removed_flags:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.REMOVE_FLAGS,
                target=case,
                payload={"removed_flags": removed_flags, "additional_text": note},
            )

    def _set_case_activity_for_goods(self, added_flags, removed_flags, case, user, note, good):
        # Add an activity item for the case
        if added_flags:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.GOOD_ADD_FLAGS,
                action_object=good,
                target=case,
                payload={"added_flags": added_flags, "good_name": good.description, "additional_text": note,},
            )

        if removed_flags:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.GOOD_REMOVE_FLAGS,
                action_object=good,
                target=case,
                payload={"removed_flags": removed_flags, "good_name": good.description, "additional_text": note},
            )

    def _set_case_activity_for_destinations(self, added_flags, removed_flags, case, user, note, destination):
        # Add an activity item for the case
        if added_flags:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.DESTINATION_ADD_FLAGS,
                action_object=destination,
                target=case,
                payload={"added_flags": added_flags, "destination_name": destination.name, "additional_text": note},
            )

        if removed_flags:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.DESTINATION_REMOVE_FLAGS,
                action_object=destination,
                target=case,
                payload={
                    "removed_flags": removed_flags,
                    "destination_name": destination.name,
                    "additional_text": note,
                },
            )

    @staticmethod
    def _get_case_for_destination(party):
        qs = StandardApplication.objects.filter(party__party=party)
        if not qs:
            qs = EndUserAdvisoryQuery.objects.filter(Q(end_user=party))

        if not qs:
            qs = HmrcQuery.objects.filter(party__party=party)
        if qs:
            return qs.first().get_case()


class FlaggingRules(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = FlaggingRuleSerializer

    def get_queryset(self):
        assert_user_has_permission(self.request.user, GovPermissions.MANAGE_FLAGGING_RULES)
        rules = FlaggingRule.objects.all()

        include_deactivated = self.request.query_params.get("include_deactivated", "")
        if not include_deactivated:
            rules = rules.filter(status=FlagStatuses.ACTIVE)

        level = self.request.query_params.get("level", "")
        if level:
            rules = rules.filter(level=level)

        only_my_team = self.request.query_params.get("only_my_team", "")
        if only_my_team:
            rules = rules.filter(team=self.request.user.team)

        return rules

    @transaction.atomic
    @swagger_auto_schema(request_body=FlaggingRuleSerializer, responses={400: "JSON parse error"})
    def post(self, request):
        assert_user_has_permission(self.request.user, GovPermissions.MANAGE_FLAGGING_RULES)
        json = request.data
        json["team"] = self.request.user.team.id
        serializer = FlaggingRuleSerializer(data=request.data)

        if serializer.is_valid():
            flagging_rule = serializer.save()
            apply_flagging_rule_to_all_open_cases(flagging_rule)
            return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class FlaggingRuleDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        assert_user_has_permission(self.request.user, GovPermissions.MANAGE_FLAGGING_RULES)
        flagging_rule = get_flagging_rule(pk)
        serializer = FlaggingRuleSerializer(flagging_rule)
        return JsonResponse(data={"flag": serializer.data})

    def put(self, request, pk):
        assert_user_has_permission(self.request.user, GovPermissions.MANAGE_FLAGGING_RULES)
        flagging_rule = get_flagging_rule(pk)

        if request.user.team != flagging_rule.team:
            return JsonResponse(data={"errors": strings.Flags.FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

        serializer = FlaggingRuleSerializer(instance=flagging_rule, data=request.data, partial=True)

        if serializer.is_valid():
            flagging_rule = serializer.save()
            apply_flagging_rule_to_all_open_cases(flagging_rule)
            return JsonResponse(data={"flagging_rule": serializer.data})

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
