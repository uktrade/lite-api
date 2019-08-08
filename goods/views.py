from django.db import transaction
from django.http import JsonResponse, Http404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from case_types.models import CaseType
from cases.models import Case
from clc_queries.models import ClcQuery
from conf.authentication import ExporterAuthentication
from documents.models import Document
from goods.enums import GoodStatus, GoodControlled
from goods.libraries.get_good import get_good, get_good_document
from goods.models import Good, GoodDocument
from goods.serializers import GoodSerializer, GoodDocumentViewSerializer, GoodDocumentCreateSerializer
from organisations.libraries.get_organisation import get_organisation_by_user
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status


class GoodList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        organisation = get_organisation_by_user(request.user)
        description = request.GET.get('description', '')
        part_number = request.GET.get('part_number', '')
        goods = Good.objects.filter(organisation=organisation,
                                    description__icontains=description,
                                    part_number__icontains=part_number).order_by('description')
        serializer = GoodSerializer(goods, many=True)
        return JsonResponse(data={'goods': serializer.data},
                            )

    def post(self, request):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        data['organisation'] = organisation.id
        data['status'] = GoodStatus.DRAFT
        serializer = GoodSerializer(data=data)

        if serializer.is_valid():
            if not data['validate_only']:
                good = serializer.save()

                if data['is_good_controlled'] == GoodControlled.UNSURE:
                    # automatically raise a CLC query case
                    clc_query = ClcQuery(details=data['not_sure_details_details'],
                                         good=good,
                                         status=get_case_status_from_status(CaseStatusEnum.SUBMITTED))
                    clc_query.save()

                    # Create a case
                    case_type = CaseType(id='b12cb700-7b19-40ab-b777-e82ce71e380f')
                    case = Case(clc_query=clc_query, case_type=case_type)
                    case.save()

                    # Add said case to default queue
                    queue = Queue.objects.get(pk='00000000-0000-0000-0000-000000000001')
                    queue.cases.add(case)
                    queue.save()

            return JsonResponse(data={'good': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class GoodDetail(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        good = get_good(pk)

        if good.organisation != organisation:
            raise Http404

        serializer = GoodSerializer(good)
        request.user.notification_set.filter(note__case__clc_query__good=good).update(
            viewed_at=timezone.now()
        )
        return JsonResponse(data={'good': serializer.data})

    def put(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        good = get_good(pk)

        if good.organisation != organisation:
            raise Http404

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(data={'errors': 'This good is already on a submitted application'},
                                status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['organisation'] = organisation.id
        serializer = GoodSerializer(instance=good, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'good': serializer.data})
        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        good = get_good(pk)

        if good.organisation != organisation:
            raise Http404

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(data={'errors': 'Good is already on a submitted application'},
                                status=status.HTTP_400_BAD_REQUEST)

        good.delete()
        return JsonResponse(data={'status': 'Good Deleted'},
                            status=status.HTTP_200_OK)


class GoodDocuments(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns a list of documents on the specified good
        """
        good = get_good(pk)
        good_documents = GoodDocument.objects.filter(good=good).order_by('-created_at')
        serializer = GoodDocumentViewSerializer(good_documents, many=True)

        return JsonResponse({'documents': serializer.data})

    @swagger_auto_schema(
        request_body=GoodDocumentCreateSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk):
        """
        Adds a document to the specified good
        """
        good = get_good(pk)
        good_id = str(good.id)
        data = request.data
        organisation = get_organisation_by_user(request.user)

        if good.organisation != organisation:
            raise Http404

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(data={'errors': 'This good is already on a submitted application'},
                                status=status.HTTP_400_BAD_REQUEST)

        for document in data:
            document['good'] = good_id
            document['user'] = request.user.id
            document['organisation'] = organisation.id

        serializer = GoodDocumentCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'documents': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse({'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class GoodDocumentDetail(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk, doc_pk):
        """
        Returns a list of documents on the specified good
        """
        good = get_good(pk)
        organisation = get_organisation_by_user(request.user)

        if good.organisation != organisation:
            raise Http404

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(data={'errors': 'This good is already on a submitted application'},
                                status=status.HTTP_400_BAD_REQUEST)

        good_document = get_good_document(good, doc_pk)
        serializer = GoodDocumentViewSerializer(good_document)
        return JsonResponse({'document': serializer.data})

    @transaction.atomic()
    def delete(self, request, pk, doc_pk):
        """
        Deletes good document
        :param request:
        :param pk:
        :param doc_pk:
        :return:
        """

        good = get_good(pk)
        organisation = get_organisation_by_user(request.user)

        if good.organisation != organisation:
            raise Http404

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(data={'errors': 'This good is already on a submitted application'},
                                status=status.HTTP_400_BAD_REQUEST)

        good_document = Document.objects.get(id=doc_pk)
        document = get_good_document(good, good_document.id)
        document.delete_s3()

        good_document.delete()

        return JsonResponse({'document': 'deleted success'})
