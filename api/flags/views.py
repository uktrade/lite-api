from django.db.models import Q
from django.http import JsonResponse

from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from api.applications.models import GoodOnApplication, StandardApplication

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType

from api.cases.libraries.get_case import get_case
from api.cases.libraries.get_flags import get_flags
from api.cases.models import Case

from api.core.authentication import GovAuthentication
from api.core.helpers import str_to_bool

from api.flags.enums import FlagLevels, FlagStatuses, SystemFlags
from api.flags.helpers import get_object_of_level
from api.flags.models import Flag
from api.flags.serializers import (
    FlagSerializer,
    FlagAssignmentSerializer,
    FlagReadOnlySerializer,
)

from api.goods.models import Good

from api.organisations.models import Organisation

from api.parties.models import Party

from api.queries.end_user_advisories.models import EndUserAdvisoryQuery
from api.queries.goods_query.models import GoodsQuery


class FlagsListView(ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = FlagReadOnlySerializer

    def get_queryset(self):
        case = self.request.GET.get("case")
        name = self.request.GET.get("name")
        level = self.request.GET.get("level")
        priority = self.request.GET.get("priority")
        team = self.request.GET.get("team")
        status = self.request.GET.get("status", FlagStatuses.ACTIVE)
        include_system_flags = str_to_bool(self.request.GET.get("include_system_flags"))
        blocks_finalising = str_to_bool(self.request.GET.get("blocks_finalising"))

        if case:
            flags = get_flags(get_case(case))
        else:
            flags = Flag.objects.exclude(level=FlagLevels.PARTY_ON_APPLICATION)

        if name:
            flags = flags.filter(name__icontains=name)

        if level:
            flags = flags.filter(level=level)

        if priority:
            flags = flags.filter(priority=priority)

        if team and team != "None":
            flags = flags.filter(team=team)

        if status:
            flags = flags.filter(status=status)

        if include_system_flags:
            system_flags = Flag.objects.filter(id__in=SystemFlags.list).exclude(level=FlagLevels.PARTY_ON_APPLICATION)
            flags = flags | system_flags

        if blocks_finalising:
            flags = flags.filter(blocks_finalising=True)

        return flags.order_by("name").select_related("team")


class FlagsRetrieveView(RetrieveAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = FlagSerializer

    def get_queryset(self):
        return Flag.objects.filter(team=self.request.user.govuser.team).exclude(level=FlagLevels.PARTY_ON_APPLICATION)


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
                data=data,
                context={
                    "team": request.user.govuser.team,
                    "level": level.title(),
                    "user": request.user.govuser,
                    "obj": obj,
                },
            )

            if serializer.is_valid():
                self._assign_flags(
                    flags=serializer.validated_data.get("flags"),
                    level=level.title(),
                    note=serializer.validated_data.get("note"),
                    obj=obj,
                    user=request.user.govuser,
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
        removed_flag_names = [flag.name for flag in previously_assigned_team_flags if flag not in ignored_flags]

        self.added_flags_id = [str(flag.id) for flag in flags if flag not in previously_assigned_team_flags]
        self.removed_flags_id = [str(flag.id) for flag in previously_assigned_team_flags if flag not in ignored_flags]

        # Add activity item

        if isinstance(obj, Case):
            self._set_case_activity(added_flags, removed_flag_names, obj, user, note)
        elif isinstance(obj, Organisation):
            self._set_organisation_activity(added_flags, removed_flag_names, obj, user, note)

        if isinstance(obj, Good):
            cases = []

            cases.extend(Case.objects.filter(id__in=GoodsQuery.objects.filter(good=obj).values_list("id", flat=True)))

            cases.extend(
                Case.objects.filter(id__in=GoodOnApplication.objects.filter(good=obj).values_list("id", flat=True))
            )

            for case in cases:
                self._set_case_activity_for_goods(added_flags, removed_flag_names, case, user, note, good=obj)

        if isinstance(obj, Party):
            case = self._get_case_for_destination(obj)
            self._set_case_activity_for_destinations(added_flags, removed_flag_names, case, user, note, destination=obj)

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
                payload={
                    "added_flags": added_flags,
                    "additional_text": note,
                    "added_flags_id": self.added_flags_id,
                },
            )

        if removed_flags:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.REMOVE_FLAGS,
                target=case,
                payload={
                    "removed_flags": removed_flags,
                    "additional_text": note,
                    "removed_flags_id": self.removed_flags_id,
                },
            )

    def _set_organisation_activity(self, added_flags, removed_flags, organisation, user, note, **kwargs):
        # Add an activity item for the organisation
        if added_flags:
            verb = AuditType.ADDED_FLAG_ON_ORGANISATION
            flags = added_flags
        elif removed_flags:
            verb = AuditType.REMOVED_FLAG_ON_ORGANISATION
            flags = removed_flags
        else:
            return

        payload = {"flag_name": flags, "additional_text": note}

        audit_trail_service.create(
            actor=user,
            verb=verb,
            target=organisation,
            payload=payload,
        )

    def _set_case_activity_for_goods(self, added_flags, removed_flags, case, user, note, good):
        # Add an activity item for the case
        if added_flags:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.GOOD_ADD_FLAGS,
                action_object=good,
                target=case,
                payload={
                    "added_flags": added_flags,
                    "good_name": good.description,
                    "additional_text": note,
                },
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
        qs = StandardApplication.objects.filter(parties__party=party)
        if not qs:
            qs = EndUserAdvisoryQuery.objects.filter(Q(end_user=party))

        if qs.exists():
            return qs.first().get_case()
