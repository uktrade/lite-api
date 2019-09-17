from django.db import transaction
from django.http.response import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from cases.libraries.activity_types import CaseActivityType
from cases.libraries.get_case import get_case, get_case_document
from cases.libraries.get_ecju_queries import get_ecju_query
from cases.libraries.mark_notifications_as_viewed import mark_notifications_as_viewed
from cases.models import CaseDocument, EcjuQuery, CaseAssignment, Advice, CaseActivity
from cases.serializers import CaseDocumentViewSerializer, CaseDocumentCreateSerializer, \
    EcjuQueryCreateSerializer, CaseDetailSerializer, \
    CaseAdviceSerializer, EcjuQueryGovSerializer, EcjuQueryExporterSerializer
from conf.authentication import GovAuthentication, SharedAuthentication
from documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from users.models import ExporterUser


class CaseDetail(APIView):
    authentication_classes = (SharedAuthentication,)

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
        self.advice = Advice.objects.filter(case=self.case)
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
