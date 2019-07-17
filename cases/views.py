import reversion
from django.db import transaction
from django.http.response import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from reversion.models import Version
from uuid import UUID

from cases.libraries.activity_helpers import convert_audit_to_activity, convert_case_note_to_activity
from cases.libraries.get_case import get_case
from cases.libraries.get_case_note import get_case_notes_from_case
from cases.models import CaseAssignment, Case
from flags.models import Flag
from cases.serializers import CaseNoteSerializer, CaseDetailSerializer, CaseFlagsAssignmentSerializer
from conf.authentication import GovAuthentication
from gov_users.models import GovUserRevisionMeta


@permission_classes((permissions.AllowAny,))
class CaseDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a case instance
        """
        case = get_case(pk)
        serializer = CaseDetailSerializer(case)
        return JsonResponse(data={'case': serializer.data})

    @swagger_auto_schema(
        responses={
            400: 'Input error, "queues" should be an array with at least one existing queue'
        })
    @transaction.atomic
    def put(self, request, pk):
        """
        Change the queues a case belongs to
        """
        case = get_case(pk)
        initial_queues = case.queues.values_list('id', flat=True)

        serializer = CaseDetailSerializer(case, data=request.data, partial=True)
        if serializer.is_valid():
            for initial_queue in initial_queues:
                if str(initial_queue) not in request.data['queues']:
                    CaseAssignment.objects.filter(queue=initial_queue).delete()

            serializer.save()

            return JsonResponse(data={'case': serializer.data},
                                status=status.HTTP_200_OK)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class CaseNoteList(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Retrieve/create case notes.
    """

    def get(self, request, pk):
        """
        Gets all case notes
        """
        case = get_case(pk)
        serializer = CaseNoteSerializer(get_case_notes_from_case(case), many=True)
        return JsonResponse(data={'case_notes': serializer.data})

    def post(self, request, pk):
        case = get_case(pk)
        data = request.data
        data['case'] = str(case.id)
        data['user'] = str(request.user.id)

        serializer = CaseNoteSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'case_note': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class ActivityList(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Retrieves all activity related to a case
    * Case Notes
    * Case Updates
    """

    def get(self, request, pk):
        case = get_case(pk)
        case_notes = get_case_notes_from_case(case)

        if case.application_id:
            version_records = Version.objects.filter(object_id=case.application.pk).order_by('-revision_id')
        else:
            version_records = {}
        activity = []

        for version in version_records:
            activity_item = convert_audit_to_activity(version)
            if activity_item:
                activity.append(activity_item)

        # Split fields into request fields
        fields = request.GET.get('fields', None)
        if fields:
            fields = fields.split(',')

            for item in activity:
                item['data'] = {your_key: item['data'][your_key] for your_key in fields}

            # Only show unique dictionaries
            for i in range(len(activity)):
                if i < len(activity) - 1:
                    activity[i]['data'] = dict(set(activity[i]['data'].items()) - set(activity[i + 1]['data'].items()))

                    if not activity[i]['data']:
                        del activity[i]

        for case_note in case_notes:
            activity.append(convert_case_note_to_activity(case_note))

        # Sort the activity based on date (newest first)
        activity.sort(key=lambda x: x['date'], reverse=True)

        return JsonResponse(data={'activity': activity})


class CaseFlagsAssignment(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        """
        Assigns flags to a case
        """
        case = get_case(str(pk))
        data = JSONParser().parse(request)

        serializer = CaseFlagsAssignmentSerializer(data=data, context={'team': request.user.team})

        if serializer.is_valid():
            self._assign_flags(serializer.validated_data.get('flags'), case, request.user)

            return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED)
        else:
            return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def _assign_flags(self, validated_data, case, user):
        previously_assigned_case_flags = case.flags.filter(level='Case', team=user.team)
        case_flags_to_add = [case_flag.name for case_flag in validated_data if case_flag not in previously_assigned_case_flags]
        case_flags_removed = [case_flag.name for case_flag in previously_assigned_case_flags if case_flag not in validated_data]

        with reversion.create_revision():
            reversion.set_comment(
                "{'removed_flags': " + str(case_flags_removed) + ", 'added_flags': " + str(case_flags_to_add) + "}"
            )
            reversion.add_meta(GovUserRevisionMeta, gov_user=user)

            case.flags.set(validated_data)
