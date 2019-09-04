from django.db import transaction
from django.http import JsonResponse, HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.get_document import get_document
from end_user.document.models import EndUserDocument
from end_user.models import EndUser
from end_user.serializers import EndUserDocumentSerializer


class EndUserDocuments(APIView):
    authentication_classes = (ExporterAuthentication,)

    def _get_end_user(self, eu_pk):
        end_users = EndUser.objects.filter(id=eu_pk)
        assert len(end_users) == 1
        return end_users.first()

    def get(self, request, pk, eu_pk):
        """
        Returns document for the specified end user
        """
        end_user = self._get_end_user(eu_pk)
        return get_document(end_user)

    @swagger_auto_schema(
        request_body=EndUserDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk, eu_pk):
        """
        Adds a document to the specified end user
        """
        end_user = self._get_end_user(eu_pk)

        if not end_user:
            return JsonResponse(data={'error': 'No such user'},
                                status=status.HTTP_400_BAD_REQUEST)

        end_user_documents = EndUserDocument.objects.filter(end_user=end_user)
        if end_user_documents:
            return JsonResponse(data={'error': 'Document already exists'},
                                status=status.HTTP_400_BAD_REQUEST)

        end_user_id = str(end_user.id)
        data = request.data

        data['end_user'] = end_user_id

        serializer = EndUserDocumentSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'document': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse({'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=EndUserDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def delete(self, request, pk, **kwargs):
        """
        Deletes a document from the specified end user
        """
        end_user = self._get_end_user(kwargs, pk)

        if not end_user:
            return JsonResponse(data={'error': 'No such user'},
                                status=status.HTTP_400_BAD_REQUEST)

        try:
            end_user_document = EndUserDocument.objects.get(end_user=end_user)
            end_user_document.delete_s3()
            end_user_document.delete()
        except EndUserDocument.DoesNotExist:
            return JsonResponse(data={'error': 'No such document'}, status=status.HTTP_400_BAD_REQUEST)

        return HttpResponse(status=204)
