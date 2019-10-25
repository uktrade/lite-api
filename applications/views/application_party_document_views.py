from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from applications.libraries.document_helpers import upload_party_document, delete_party_document, get_party_document
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users, application_in_major_editable_state, application_licence_type
from parties.document.serializers import PartyDocumentSerializer
from parties.libraries.get_parties import get_end_user, get_ultimate_end_user, get_consignee, get_third_party
from users.models import ExporterUser


class EndUserDocumentView(APIView):
    """
    Retrieve, add or delete an end user document from an application
    """
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def get(self, request, application):
        end_user = get_end_user(application.pk)
        return get_party_document(end_user)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        end_user = get_end_user(application.pk)
        return upload_party_document(end_user, request.data, application.id, request.user)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def delete(self, request, application):
        end_user = get_end_user(application.pk)
        return delete_party_document(end_user, application.id, request.user)


class UltimateEndUserDocumentsView(APIView):
    """
    Retrieve, add or delete an ultimate end user document from an application
    """
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def get(self, request, application, ueu_pk):
        ultimate_end_user = get_ultimate_end_user(ueu_pk)
        return get_party_document(ultimate_end_user)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application, ueu_pk):
        ultimate_end_user = get_ultimate_end_user(ueu_pk)
        return upload_party_document(ultimate_end_user, request.data, application.id, request.user)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def delete(self, request, application, ueu_pk):
        ultimate_end_user = get_ultimate_end_user(ueu_pk)
        return delete_party_document(ultimate_end_user, application.id, request.user)


class ConsigneeDocumentView(APIView):
    """
    Retrieve, add or delete a consignee document from an application
    """
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def get(self, request, application):
        consignee = get_consignee(application.pk)
        return get_party_document(consignee)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        consignee = get_consignee(application.pk)
        return upload_party_document(consignee, request.data, application.id, request.user)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def delete(self, request, application):
        consignee = get_consignee(application.pk)
        return delete_party_document(consignee, application.id, request.user)


class ThirdPartyDocumentView(APIView):
    """
    Retrieve, add or delete a third party document from an application
    """
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def get(self, request, application, tp_pk):
        third_party = get_third_party(tp_pk)
        return get_party_document(third_party)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application, tp_pk):
        third_party = get_third_party(tp_pk)
        return upload_party_document(third_party, request.data, application.id, request.user)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def delete(self, request, application, tp_pk):
        third_party = get_third_party(tp_pk)
        return delete_party_document(third_party, application.id, request.user)
