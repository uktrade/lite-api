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
from cases.libraries.get_case_flags import get_case_flags_from_case
from cases.models import CaseAssignment, CaseFlags
from flags.models import Flag
from cases.serializers import CaseNoteSerializer, CaseDetailSerializer, CaseFlagSerializer
from conf.authentication import GovAuthentication


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


class CaseFlagsList(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieves all flags related to a case
        """
        case_flags = get_case_flags_from_case(str(pk))
        serializer = CaseFlagSerializer(case_flags, context={'method': request.method}, many=True)

        return JsonResponse(data={'case_flags': serializer.data})

    def post(self, request, pk):
        """
        Assigns flags to a case
        """
        case = str(pk)
        data = JSONParser().parse(request)
        case_flags = []

        for flag in data['flags']:
            case_flags.append({'case': case, 'flag': flag})

        team_case_level_flags = Flag.objects.filter(level='Case', team=request.user.team.id)

        serializer = CaseFlagSerializer(data=case_flags, context={
                'method': request.method,
                'team_case_level_flags': team_case_level_flags
            }, many=True)

        if serializer.is_valid():
            previously_assigned_team_case_level_flags = CaseFlags.objects.filter(case=case, flag__level='Case', flag__team=request.user.team.id)

            # Delete case_flags that aren't in validated_data
            for previously_assigned_flag in previously_assigned_team_case_level_flags:
                delete_case_flag = True
                for validated_case_flag in serializer.validated_data:
                    if previously_assigned_flag.flag == validated_case_flag.get('flag'):
                        delete_case_flag = False
                        break
                if delete_case_flag:
                    previously_assigned_flag.delete()

            # Add case_flags in validated_data if not already present
            for validated_case_flag in serializer.validated_data:
                add_case_flag = True
                for previously_assigned_flag in previously_assigned_team_case_level_flags:
                    if validated_case_flag.get('flag') == previously_assigned_flag.flag:
                        add_case_flag = False
                if add_case_flag:
                    case_flag = CaseFlags(case=validated_case_flag.get('case'), flag=validated_case_flag.get('flag'))
                    case_flag.save()

            return JsonResponse(data={'case_flags': serializer.data},
                                status=status.HTTP_201_CREATED)
        else:
            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
