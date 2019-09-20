from django.db import transaction
from django.http.response import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from cases.helpers import create_grouped_advice
from cases.libraries.activity_types import CaseActivityType
from cases.libraries.get_case import get_case, get_case_document
from cases.libraries.get_ecju_queries import get_ecju_query
from cases.libraries.mark_notifications_as_viewed import mark_notifications_as_viewed
from cases.models import CaseDocument, EcjuQuery, CaseAssignment, Advice, TeamAdvice, FinalAdvice, CaseActivity
from cases.serializers import CaseDocumentViewSerializer, CaseDocumentCreateSerializer, \
    EcjuQueryCreateSerializer, CaseDetailSerializer, \
    CaseAdviceSerializer, EcjuQueryGovSerializer, EcjuQueryExporterSerializer, CaseTeamAdviceSerializer, CaseFinalAdviceSerializer
from conf.authentication import GovAuthentication, SharedAuthentication
from content_strings.strings import get_string
from conf.constants import Permissions
from conf.permissions import assert_user_has_permission
from documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from teams.helpers import get_team_by_pk
from users.models import ExporterUser


class CaseDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a case instance
        """
        case = get_case(pk)
        serializer = CaseDetailSerializer(case, context=request)

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

            # Add an activity item for the query's case
            CaseActivity.create(activity_type=CaseActivityType.MOVE_CASE,
                                case=case,
                                user=request.user,
                                queues=[x.name for x in serializer.validated_data['queues']])

            return JsonResponse(data={'case': serializer.data})

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class CaseDocuments(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Returns a list of documents on the specified case
        """
        case = get_case(pk)
        case_documents = CaseDocument.objects.filter(case=case).order_by('-created_at')
        serializer = CaseDocumentViewSerializer(case_documents, many=True)

        return JsonResponse({'documents': serializer.data})

    @swagger_auto_schema(
        request_body=CaseDocumentCreateSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk):
        """
        Adds a document to the specified case
        """
        case = get_case(pk)
        case_id = str(case.id)
        data = request.data

        for document in data:
            document['case'] = case_id
            document['user'] = request.user.id

        serializer = CaseDocumentCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'documents': serializer.data}, status=status.HTTP_201_CREATED)

        delete_documents_on_bad_request(data)
        return JsonResponse({'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class CaseDocumentDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk, s3_key):
        """
        Returns a list of documents on the specified case
        """
        case = get_case(pk)
        case_document = get_case_document(case, s3_key)
        serializer = CaseDocumentViewSerializer(case_document)
        return JsonResponse({'document': serializer.data})


class CaseAdvice(APIView):
    authentication_classes = (GovAuthentication,)

    case = None
    advice = None
    serializer_object = None

    def dispatch(self, request, *args, **kwargs):
        self.case = get_case(kwargs['pk'])
        # We exclude any team of final level advice objects
        self.advice = Advice.objects.filter(case=self.case)\
            .exclude(teamadvice__isnull=False)\
            .exclude(finaladvice__isnull=False)
        self.serializer_object = CaseAdviceSerializer

        return super(CaseAdvice, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """
        Returns all advice for a case
        """
        serializer = self.serializer_object(self.advice, many=True)
        return JsonResponse({'advice': serializer.data})

    def post(self, request, pk):
        """
        Creates advice for a case
        """
        if FinalAdvice.objects.filter(case=self.case):
            return JsonResponse({'errors': 'Final advice already exists for this case'},
                                status=status.HTTP_400_BAD_REQUEST)

        if TeamAdvice.objects.filter(case=self.case, team=self.request.user.team):
            return JsonResponse({'errors': 'Team advice from your team already exists for this case'},
                                status=status.HTTP_400_BAD_REQUEST)

        data = request.data

        # Update the case and user in each piece of advice
        for advice in data:
            advice['case'] = str(self.case.id)
            advice['user'] = str(request.user.id)

        serializer = self.serializer_object(data=data, many=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'advice': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ViewTeamAdvice(APIView):
    def get(self, request, pk, team_pk):
        case = get_case(pk)
        team = get_team_by_pk(team_pk)
        team_advice = TeamAdvice.objects.filter(case=case, team=team)

        serializer = CaseTeamAdviceSerializer(team_advice, many=True)
        return JsonResponse({'advice': serializer.data})


class CaseTeamAdvice(APIView):
    authentication_classes = (GovAuthentication,)

    case = None
    advice = None
    team_advice = None
    serializer_object = None

    def dispatch(self, request, *args, **kwargs):
        self.case = get_case(kwargs['pk'])
        self.advice = Advice.objects.filter(case=self.case)
        self.team_advice = TeamAdvice.objects.filter(case=self.case)
        self.serializer_object = CaseTeamAdviceSerializer

        return super(CaseTeamAdvice, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """
        Concatenates all advice for a case and returns it or just returns if team advice already exists
        """
        if self.team_advice.filter(team=request.user.team).count() == 0:
            # We pass in the class of advice we are creating
            assert_user_has_permission(request.user, Permissions.MANAGE_TEAM_ADVICE)
            team = self.request.user.team
            advice = self.advice.filter(user__team=team)
            create_grouped_advice(self.case, self.request, advice, TeamAdvice)
            CaseActivity.create(activity_type=CaseActivityType.CREATED_TEAM_ADVICE,
                                case=self.case,
                                user=request.user)
            team_advice = TeamAdvice.objects.filter(case=self.case, team=team)
        else:
            team_advice = self.team_advice
        serializer = self.serializer_object(team_advice, many=True)
        return JsonResponse({'advice': serializer.data})

    def post(self, request, pk):
        """
        Creates advice for a case
        """
        assert_user_has_permission(request.user, Permissions.MANAGE_TEAM_ADVICE)
        if FinalAdvice.objects.filter(case=self.case):
            return JsonResponse({'errors': 'Final advice already exists for this case'},
                                status=status.HTTP_400_BAD_REQUEST)

        data = request.data

        # Update the case and user in each piece of advice
        for advice in data:
            advice['case'] = str(self.case.id)
            advice['user'] = str(request.user.id)
            advice['team'] = str(request.user.team.id)

        serializer = self.serializer_object(data=data, many=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'advice': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Clears team level advice and reopens the advice for user level for that team
        """
        assert_user_has_permission(request.user, Permissions.MANAGE_TEAM_ADVICE)
        self.team_advice.filter(team=self.request.user.team).delete()
        CaseActivity.create(activity_type=CaseActivityType.CLEARED_TEAM_ADVICE,
                            case=self.case,
                            user=request.user)
        return JsonResponse({'status': 'success'}, status=status.HTTP_200_OK)


class ViewFinalAdvice(APIView):
    def get(self, request, pk):
        case = get_case(pk)
        final_advice = FinalAdvice.objects.filter(case=case)

        serializer = CaseFinalAdviceSerializer(final_advice, many=True)
        return JsonResponse({'advice': serializer.data})


class CaseFinalAdvice(APIView):
    authentication_classes = (GovAuthentication,)

    case = None
    team_advice = None
    final_advice = None
    serializer_object = None

    def dispatch(self, request, *args, **kwargs):
        self.case = get_case(kwargs['pk'])
        self.team_advice = TeamAdvice.objects.filter(case=self.case)
        self.final_advice = FinalAdvice.objects.filter(case=self.case)
        self.serializer_object = CaseFinalAdviceSerializer

        return super(CaseFinalAdvice, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """
        Concatenates all advice for a case and returns it or just returns if team advice already exists
        """
        if len(self.final_advice) == 0:
            assert_user_has_permission(request.user, Permissions.MANAGE_FINAL_ADVICE)
            # We pass in the class of advice we are creating
            create_grouped_advice(self.case, self.request, self.team_advice, FinalAdvice)
            CaseActivity.create(activity_type=CaseActivityType.CREATED_FINAL_ADVICE,
                                case=self.case,
                                user=request.user)
            final_advice = FinalAdvice.objects.filter(case=self.case)
        else:
            final_advice = self.final_advice
        serializer = self.serializer_object(final_advice, many=True)
        return JsonResponse({'advice': serializer.data})

    @swagger_auto_schema(
        request_body=CaseFinalAdviceSerializer,
        responses={
            400: 'JSON parse error'
        })
    def post(self, request, pk):
        """
        Creates advice for a case
        """
        assert_user_has_permission(request.user, Permissions.MANAGE_FINAL_ADVICE)
        data = request.data

        # Update the case and user in each piece of advice
        for advice in data:
            advice['case'] = str(self.case.id)
            advice['user'] = str(request.user.id)
            if advice['type'].lower() == 'refuse' and not advice['text']:
                return JsonResponse(
                    {'errors': [
                        {'text': [ErrorDetail(string=get_string('cases.advice_refusal_error'), code='blank')]}
                    ]}, status=status.HTTP_400_BAD_REQUEST)
            advice['team'] = str(request.user.team.id)

        serializer = self.serializer_object(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'advice': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Clears team level advice and reopens the advice for user level for that team
        """
        assert_user_has_permission(request.user, Permissions.MANAGE_FINAL_ADVICE)
        self.final_advice.delete()
        CaseActivity.create(activity_type=CaseActivityType.CLEARED_FINAL_ADVICE,
                            case=self.case,
                            user=request.user)
        return JsonResponse({'status': 'success'}, status=status.HTTP_200_OK)


class CaseEcjuQueries(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        """
        Returns the list of ECJU Queries on a case
        """
        case = get_case(pk)
        case_ecju_queries = EcjuQuery.objects.filter(case=case)

        if isinstance(request.user, ExporterUser):
            serializer = EcjuQueryExporterSerializer(case_ecju_queries, many=True)
        else:
            serializer = EcjuQueryGovSerializer(case_ecju_queries, many=True)

        mark_notifications_as_viewed(request.user, case_ecju_queries)

        return JsonResponse({'ecju_queries': serializer.data})

    def post(self, request, pk):
        """
        Add a new ECJU query
        """
        data = JSONParser().parse(request)
        data['case'] = pk
        data['raised_by_user'] = request.user.id
        serializer = EcjuQueryCreateSerializer(data=data)

        if serializer.is_valid():
            if 'validate_only' not in data or not data['validate_only']:
                serializer.save()

                CaseActivity.create(activity_type=CaseActivityType.ECJU_QUERY,
                                    case=get_case(pk),
                                    user=request.user,
                                    ecju_query=data['question'])

                return JsonResponse(data={'ecju_query_id': serializer.data['id']},
                                    status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={}, status=status.HTTP_200_OK)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class EcjuQueryDetail(APIView):
    """
    Details of a specific ECJU query
    """
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk, ecju_pk):
        """
        Returns details of an ecju query
        """
        ecju_query = get_ecju_query(ecju_pk)
        serializer = EcjuQueryExporterSerializer(ecju_query)
        return JsonResponse(data={'ecju_query': serializer.data})

    def put(self, request, pk, ecju_pk):
        """
        If not validate only Will update the ecju query instance, with a response, and return the data details.
        If validate only, this will return if the data is acceptable or not.
        """
        ecju_query = get_ecju_query(ecju_pk)

        data = {
            'response': request.data['response'],
            'responded_by_user': str(request.user.id)
        }

        serializer = EcjuQueryExporterSerializer(instance=ecju_query, data=data, partial=True)

        if serializer.is_valid():
            if 'validate_only' not in request.data or not request.data['validate_only']:
                serializer.save()

                return JsonResponse(data={'ecju_query': serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={}, status=status.HTTP_200_OK)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
