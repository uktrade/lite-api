from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, Http404, HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.models import GoodOnApplication, BaseApplication
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.libraries.delete_notifications import delete_exporter_notifications
from cases.libraries.get_case import get_case
from conf import constants
from conf.authentication import ExporterAuthentication, SharedAuthentication, GovAuthentication
from conf.helpers import str_to_bool
from conf.permissions import assert_user_has_permission
from documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from documents.models import Document
from goods.enums import GoodStatus, GoodPVGraded
from goods.goods_paginator import GoodListPaginator
from goods.libraries.get_goods import get_good, get_good_document
from goods.models import Good, GoodDocument
from goods.serializers import (
    GoodSerializer,
    GoodDocumentViewSerializer,
    GoodDocumentCreateSerializer,
    ClcControlGoodSerializer,
    GoodListSerializer,
    GoodWithFlagsSerializer,
    GoodMissingDocumentSerializer,
    GoodPvGradingDetailsSerializer,
)
from lite_content.lite_api import strings
from queries.control_list_classifications.models import ControlListClassificationQuery
from static.statuses.enums import CaseStatusEnum
from users.models import ExporterUser


class GoodsListControlCode(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def post(self, request, case_pk):
        """
        Set control list codes on multiple goods.
        """
        assert_user_has_permission(request.user, constants.GovPermissions.REVIEW_GOODS)

        application = BaseApplication.objects.get(id=case_pk)

        if CaseStatusEnum.is_terminal(application.status.status):
            return JsonResponse(
                data={"errors": [strings.Applications.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = JSONParser().parse(request)
        objects = data.get("objects")

        if not isinstance(objects, list):
            objects = [objects]

        serializer = ClcControlGoodSerializer(data=data)

        if serializer.is_valid():
            error_occurred = False
            case = get_case(case_pk)

            for pk in objects:
                try:
                    good = get_good(pk)
                    old_control_code = good.control_code
                    if not old_control_code:
                        old_control_code = "No control code"

                    new_control_code = "No control code"
                    if data.get("is_good_controlled", "no").lower() == "yes":
                        new_control_code = data.get("control_code", "No control code")

                    serializer = ClcControlGoodSerializer(good, data=data)
                    if serializer.is_valid():
                        serializer.save()

                    if new_control_code != old_control_code:
                        audit_trail_service.create(
                            actor=request.user,
                            verb=AuditType.GOOD_REVIEWED,
                            action_object=good,
                            target=case,
                            payload={
                                "good_name": good.description,
                                "new_control_code": new_control_code,
                                "old_control_code": old_control_code,
                            },
                        )
                except Http404:
                    error_occurred = True

            if not error_occurred:
                return HttpResponse(status=status.HTTP_200_OK)
            else:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class GoodList(ListCreateAPIView):
    model = Good
    authentication_classes = (ExporterAuthentication,)
    serializer_class = GoodListSerializer
    pagination_class = GoodListPaginator

    def get_serializer_context(self):
        return {"exporter_user": self.request.user}

    def get_queryset(self):
        description = self.request.GET.get("description", "")
        part_number = self.request.GET.get("part_number", "")
        control_rating = self.request.GET.get("control_rating")
        for_application = self.request.GET.get("for_application")
        organisation = self.request.user.organisation.id

        queryset = Good.objects.filter(
            organisation_id=organisation, description__icontains=description, part_number__icontains=part_number,
        ).order_by("-created_at")

        if control_rating:
            queryset = queryset.filter(control_code__icontains=control_rating)

        if for_application:
            good_document_ids = GoodDocument.objects.filter(organisation__id=organisation).values_list(
                "good", flat=True
            )
            queryset = queryset.filter(Q(id__in=good_document_ids) | Q(missing_document_reason__isnull=False))

        return queryset

    def post(self, request, *args, **kwargs):
        """
        Add a good to to an organisation
        """
        data = request.data
        data["organisation"] = request.user.organisation.id
        data["status"] = GoodStatus.DRAFT

        serializer = GoodSerializer(data=data)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if "validate_only" in data and data["validate_only"] is True:
            return HttpResponse(status=status.HTTP_200_OK)
        else:
            serializer.save()

            return JsonResponse(data={"good": serializer.data}, status=status.HTTP_201_CREATED)


class GoodDocumentCriteriaCheck(APIView):
    authentication_classes = (ExporterAuthentication,)

    def post(self, request, pk):
        good = get_good(pk)
        data = request.data
        if data.get("has_document_to_upload"):
            document_to_upload = str_to_bool(data["has_document_to_upload"])
            if not document_to_upload:
                good.missing_document_reason = data["missing_document_reason"]
                serializer = GoodMissingDocumentSerializer(instance=good, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    good_data = GoodSerializer(good).data
                else:
                    return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            else:
                good_data = GoodSerializer(good).data
        else:
            return JsonResponse(
                data={"errors": {"has_document_to_upload": [strings.Goods.DOCUMENT_CHECK_OPTION_NOT_SELECTED]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return JsonResponse(data={"good": good_data}, status=status.HTTP_200_OK)


class GoodDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        good = get_good(pk)

        if isinstance(request.user, ExporterUser):
            if good.organisation != request.user.organisation:
                raise Http404

            serializer = GoodSerializer(good, context={"exporter_user": request.user})

            # If there's a query with this good, update the notifications on it
            query = ControlListClassificationQuery.objects.filter(good=good)
            if query:
                delete_exporter_notifications(user=request.user, organisation=request.user.organisation, objects=query)
        else:
            serializer = GoodWithFlagsSerializer(good)

        return JsonResponse(data={"good": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        good = get_good(pk)

        if good.organisation != request.user.organisation:
            raise Http404

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()

        if data.get("is_good_controlled") == "unsure":
            for good_on_application in GoodOnApplication.objects.filter(good=good):
                good_on_application.delete()

        data["organisation"] = request.user.organisation.id
        serializer = GoodSerializer(instance=good, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"good": serializer.data})
        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        good = get_good(pk)

        if good.organisation != request.user.organisation:
            raise Http404

        if good.status != GoodStatus.DRAFT:
            return JsonResponse(
                data={"errors": "Good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        for document in GoodDocument.objects.filter(good=good):
            document.delete_s3()

        good.delete()
        return JsonResponse(data={"status": "Good Deleted"}, status=status.HTTP_200_OK)


class GoodDocuments(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns a list of documents on the specified good
        """
        good = get_good(pk)
        good_documents = GoodDocument.objects.filter(good=good).order_by("-created_at")
        serializer = GoodDocumentViewSerializer(good_documents, many=True)

        return JsonResponse({"documents": serializer.data})

    @swagger_auto_schema(request_body=GoodDocumentCreateSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    def post(self, request, pk):
        """
        Adds a document to the specified good
        """
        good = get_good(pk)
        good_id = str(good.id)
        data = request.data

        if good.organisation != request.user.organisation:
            delete_documents_on_bad_request(data)
            raise Http404

        if good.status != GoodStatus.DRAFT:
            delete_documents_on_bad_request(data)
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        for document in data:
            document["good"] = good_id
            document["user"] = request.user.id
            document["organisation"] = request.user.organisation.id

        serializer = GoodDocumentCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            # Delete missing document reason as a document has now been uploaded
            good.missing_document_reason = None
            good.save()
            return JsonResponse({"documents": serializer.data}, status=status.HTTP_201_CREATED)

        delete_documents_on_bad_request(data)
        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class GoodDocumentDetail(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk, doc_pk):
        """
        Returns a list of documents on the specified good
        """
        good = get_good(pk)

        if good.organisation != request.user.organisation:
            raise Http404

        if good.status != GoodStatus.DRAFT:
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        good_document = get_good_document(good, doc_pk)
        serializer = GoodDocumentViewSerializer(good_document)
        return JsonResponse({"document": serializer.data})

    @transaction.atomic
    def delete(self, request, pk, doc_pk):
        """
        Deletes good document
        """
        good = get_good(pk)

        if good.organisation != request.user.organisation:
            raise Http404

        if good.status != GoodStatus.DRAFT:
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        good_document = Document.objects.get(id=doc_pk)
        document = get_good_document(good, good_document.id)
        document.delete_s3()

        good_document.delete()
        if GoodDocument.objects.filter(good=good).count() == 0:
            for good_on_application in GoodOnApplication.objects.filter(good=good):
                good_on_application.delete()

        return JsonResponse({"document": "deleted success"})
