from django.db import transaction
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationType
from applications.libraries.document_helpers import (
    upload_party_document,
    delete_party_document,
    get_party_document,
)
from applications.models import PartyOnApplication
from conf.authentication import ExporterAuthentication
from conf.decorators import (
    authorised_users,
    application_in_major_editable_state,
    allowed_application_types,
)
from parties.enums import PartyType
from parties.serializers import PartyDocumentSerializer
from users.models import ExporterUser


class EndUserDocumentView(APIView):
    """
    Retrieve, add or delete an end user document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def get(self, request, application):
        try:
            party = PartyOnApplication.objects.get(
                application=application,
                party__type=PartyType.END_USER,
                deleted_at__isnull=True
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)

        return get_party_document(party)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        try:
            party = PartyOnApplication.objects.get(
                application=application,
                party__type=PartyType.END_USER,
                deleted_at__isnull=True
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)

        return upload_party_document(party, request.data, application, request.user)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def delete(self, request, application):
        try:
            party = PartyOnApplication.objects.get(
                application=application,
                party__type=PartyType.END_USER,
                deleted_at__isnull=True
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)

        return delete_party_document(party, application, request.user)


class UltimateEndUserDocumentsView(APIView):
    """
    Retrieve, add or delete an ultimate end user document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def get(self, request, application, party_pk):
        try:
            party = PartyOnApplication.objects.get(
                application=application,
                party__type=PartyType.ULTIMATE_END_USER,
                deleted_at__isnull=True
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)

        return get_party_document(party)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application, party_pk):
        try:
            party = PartyOnApplication.objects.get(
                application=application,
                party__type=PartyType.ULTIMATE_END_USER,
                deleted_at__isnull=True
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)

        return upload_party_document(party, request.data, application, request.user)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def delete(self, request, application, party_pk):
        try:
            party = PartyOnApplication.objects.get(
                application=application,
                party__type=PartyType.ULTIMATE_END_USER,
                deleted_at__isnull=True
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)
        return delete_party_document(party, application, request.user)


class ConsigneeDocumentView(APIView):
    """
    Retrieve, add or delete a consignee document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def get(self, request, application):
        try:
            party = PartyOnApplication.objects.get(
                application=application, party__type=PartyType.CONSIGNEE, deleted_at__isnull=True,
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)
        return get_party_document(party)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        try:
            party = PartyOnApplication.objects.get(
                application=application, party__type=PartyType.CONSIGNEE, deleted_at__isnull=True,
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)
        return upload_party_document(party, request.data, application, request.user)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def delete(self, request, application):
        try:
            party = PartyOnApplication.objects.get(
                application=application, party__type=PartyType.CONSIGNEE, deleted_at__isnull=True,
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)
        return delete_party_document(party, application, request.user)


class ThirdPartyDocumentView(APIView):
    """
    Retrieve, add or delete a third party document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def get(self, request, application, party_pk):
        try:
            party = PartyOnApplication.objects.get(
                application=application, party__type=PartyType.THIRD_PARTY, deleted_at__isnull=True,
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)
        return get_party_document(party)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application, party_pk):
        try:
            party = PartyOnApplication.objects.get(
                application=application, party__type=PartyType.THIRD_PARTY, deleted_at__isnull=True,
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)
        return upload_party_document(party, request.data, application, request.user)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def delete(self, request, application, party_pk):
        try:
            party = PartyOnApplication.objects.get(
                application=application, party__type=PartyType.THIRD_PARTY, deleted_at__isnull=True,
            ).party
        except PartyOnApplication.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_404_NOT_FOUND)
        return delete_party_document(party, application, request.user)
