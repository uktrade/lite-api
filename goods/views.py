from django.db import transaction
from django.http import JsonResponse, Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication, SharedAuthentication
from conf.serializers import response_serializer
from documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from documents.models import Document
from drafts.models import GoodOnDraft
from goods.helpers import if_status_unsure_remove_from_draft, bad_request_if_submitted, add_organisation_to_data, update_notifications
from goods.libraries.get_good import get_good, get_good_document
from goods.models import Good, GoodDocument
from goods.serializers import GoodSerializer, GoodDocumentViewSerializer, GoodDocumentCreateSerializer, \
    FullGoodSerializer
from organisations.libraries.get_organisation import get_organisation_by_user
from users.models import ExporterUser


class GoodList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        Returns a list of all goods belonging to an organisation
        """
        organisation = get_organisation_by_user(request.user)
        description = request.GET.get('description', '')
        part_number = request.GET.get('part_number', '')
        control_rating = request.GET.get('control_rating', '')
        goods = Good.objects.filter(organisation=organisation,
                                    description__icontains=description,
                                    part_number__icontains=part_number,
                                    control_code__icontains=control_rating).order_by('description')

        return response_serializer(GoodSerializer, obj=goods, many=True)

    def post(self, request):
        """
        Returns a list of all goods belonging to an organisation
        """
        data = JSONParser().parse(request)

        return response_serializer(GoodSerializer,
                                   data=data,
                                   object_class=Good,
                                   request=request,
                                   pre_validation_actions=[add_organisation_to_data])


class GoodDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        if isinstance(request.user, ExporterUser):
            return response_serializer(GoodSerializer,
                                       pk=pk,
                                       object_class=Good,
                                       check_organisation=True,
                                       request=request,
                                       post_get_actions=[update_notifications])

        else:
            return response_serializer(FullGoodSerializer, object_class=Good, pk=pk)

    def put(self, request, pk):
        data = request.data.copy()
        return response_serializer(GoodSerializer,
                                   pk=pk,
                                   object_class=Good,
                                   data=data,
                                   partial=True,
                                   check_organisation=True,
                                   request=request,
                                   pre_validation_actions=[
                                       bad_request_if_submitted,
                                       if_status_unsure_remove_from_draft,
                                       add_organisation_to_data
                                   ])

    def delete(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        good = get_good(pk)

        if good.organisation != organisation:
            raise Http404

        response = bad_request_if_submitted(None, None, good)
        if isinstance(response, JsonResponse):
            return response

        for document in GoodDocument.objects.filter(good=good):
            document.delete_s3()

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
        return response_serializer(GoodDocumentViewSerializer, obj=good_documents, many=True, response_name='documents')

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
            delete_documents_on_bad_request(data)
            raise Http404

        response = bad_request_if_submitted(None, None, good)
        if isinstance(response, JsonResponse):
            return response

        for document in data:
            document['good'] = good_id
            document['user'] = request.user.id
            document['organisation'] = organisation.id

        return response_serializer(GoodDocumentCreateSerializer, data=data, many=True, response_name='documents')


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

        response = bad_request_if_submitted(None, None, good)
        if isinstance(response, JsonResponse):
            return response

        good_document = get_good_document(good, doc_pk)
        serializer = GoodDocumentViewSerializer(good_document)
        return JsonResponse({'document': serializer.data})

    @transaction.atomic()
    def delete(self, request, pk, doc_pk):
        """
        Deletes good document
        """

        good = get_good(pk)
        organisation = get_organisation_by_user(request.user)

        if good.organisation != organisation:
            raise Http404

        response = bad_request_if_submitted(None, None, good)
        if isinstance(response, JsonResponse):
            return response

        good_document = Document.objects.get(id=doc_pk)
        document = get_good_document(good, good_document.id)
        document.delete_s3()

        good_document.delete()
        if len(GoodDocument.objects.filter(good=good)) == 0:
            for good_on_draft in GoodOnDraft.objects.filter(good=good):
                good_on_draft.delete()

        return JsonResponse({'document': 'deleted success'})
