from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from applications.enums import GoodsTypeCategory
from applications.libraries.document_helpers import upload_party_document, delete_party_document, get_party_document
from cases.enums import CaseTypeSubTypeEnum
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users, allowed_application_types
from conf.exceptions import BadRequestError
from parties.serializers import PartyDocumentSerializer
from users.models import ExporterUser


class PartyDocumentView(APIView):
    """
    Retrieve, add or delete an end user document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [
            CaseTypeSubTypeEnum.STANDARD,
            CaseTypeSubTypeEnum.HMRC,
            CaseTypeSubTypeEnum.EXHIBITION,
            CaseTypeSubTypeEnum.GIFTING,
            CaseTypeSubTypeEnum.F680,
            CaseTypeSubTypeEnum.OPEN,
        ]
    )
    @authorised_users(ExporterUser)
    def get(self, request, application, party_pk):
        if application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN and application.goodstype_category not in [
            GoodsTypeCategory.CRYPTOGRAPHIC,
            GoodsTypeCategory.MILITARY,
        ]:
            raise BadRequestError(detail="You cannot do this action for this type of open application")

        party = application.get_party(party_pk)
        return get_party_document(party)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @allowed_application_types(
        [
            CaseTypeSubTypeEnum.STANDARD,
            CaseTypeSubTypeEnum.HMRC,
            CaseTypeSubTypeEnum.EXHIBITION,
            CaseTypeSubTypeEnum.GIFTING,
            CaseTypeSubTypeEnum.F680,
            CaseTypeSubTypeEnum.OPEN,
        ]
    )
    @authorised_users(ExporterUser)
    def post(self, request, application, party_pk):
        if application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN and application.goodstype_category not in [
            GoodsTypeCategory.CRYPTOGRAPHIC,
            GoodsTypeCategory.MILITARY,
        ]:
            raise BadRequestError(detail="You cannot do this action for this type of open application")

        party = application.get_party(party_pk)
        return upload_party_document(party, request.data, application, request.user)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @allowed_application_types(
        [
            CaseTypeSubTypeEnum.STANDARD,
            CaseTypeSubTypeEnum.HMRC,
            CaseTypeSubTypeEnum.EXHIBITION,
            CaseTypeSubTypeEnum.GIFTING,
            CaseTypeSubTypeEnum.F680,
            CaseTypeSubTypeEnum.OPEN,
        ]
    )
    @authorised_users(ExporterUser)
    def delete(self, request, application, party_pk):
        if application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN and application.goodstype_category not in [
            GoodsTypeCategory.CRYPTOGRAPHIC,
            GoodsTypeCategory.MILITARY,
        ]:
            raise BadRequestError(detail="You cannot do this action for this type of open application")

        party = application.get_party(party_pk)
        return delete_party_document(party, application, request.user)
