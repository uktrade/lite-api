from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Count
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.views import APIView

from api.applications.models import GoodOnApplication, BaseApplication
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from cases.enums import CaseTypeSubTypeEnum
from cases.libraries.delete_notifications import delete_exporter_notifications
from cases.libraries.get_case import get_case
from api.conf import constants
from api.conf.authentication import ExporterAuthentication, SharedAuthentication, GovAuthentication
from api.conf.exceptions import BadRequestError
from api.conf.helpers import str_to_bool
from api.conf.permissions import assert_user_has_permission
from api.documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from api.documents.models import Document
from api.goods.enums import GoodStatus, GoodControlled, GoodPvGraded, ItemCategory
from api.goods.goods_paginator import GoodListPaginator
from api.goods.helpers import (
    check_if_firearm_details_edited_on_unsupported_good,
    check_if_unsupported_fields_edited_on_firearm_good,
)
from api.goods.libraries.get_goods import get_good, get_good_document
from api.goods.libraries.save_good import create_or_update_good
from api.goods.models import Good, GoodDocument
from api.goods.serializers import (
    GoodCreateSerializer,
    GoodDocumentViewSerializer,
    GoodDocumentCreateSerializer,
    ClcControlGoodSerializer,
    GoodListSerializer,
    GoodSerializerInternal,
    GoodSerializerExporter,
    GoodSerializerExporterFullDetail,
    GoodMissingDocumentSerializer,
    TinyGoodDetailsSerializer,
)
from api.goodstype.helpers import get_goods_type
from api.goodstype.serializers import ClcControlGoodTypeSerializer
from lite_content.lite_api import strings
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.queries.goods_query.models import GoodsQuery
from static.statuses.enums import CaseStatusEnum
from api.users.models import ExporterUser, ExporterNotification
from workflow.flagging_rules_automation import apply_good_flagging_rules_for_case


class GoodsListControlCode(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def post(self, request, case_pk):
        """
        Set control list codes on multiple goods.
        """
        assert_user_has_permission(request.user, constants.GovPermissions.REVIEW_GOODS)

        case = get_case(case_pk)
        application = BaseApplication.objects.get(id=case_pk)

        if CaseStatusEnum.is_terminal(application.status.status):
            return JsonResponse(
                data={"errors": {"error": [strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data
        objects = data.get("objects")

        if application.case_type.sub_type not in [CaseTypeSubTypeEnum.OPEN, CaseTypeSubTypeEnum.HMRC]:
            serializer_class = ClcControlGoodSerializer
            get_good_func = get_good
        else:
            serializer_class = ClcControlGoodTypeSerializer
            get_good_func = get_goods_type

        if not isinstance(objects, list):
            objects = [objects]

        for good_id in objects:
            good = get_good_func(good_id)
            serializer = serializer_class(good, data=data)
            if serializer.is_valid(raise_exception=True):
                # Get the old control list entries if any and retrieve their ratings for display in the audit trail
                old_control_list_entries = list(good.control_list_entries.all()) or [strings.Goods.GOOD_NO_CONTROL_CODE]
                if strings.Goods.GOOD_NO_CONTROL_CODE not in old_control_list_entries:
                    old_control_list_entries = [clc.rating for clc in old_control_list_entries]

                serializer.save()

                new_control_list_entries = list(good.control_list_entries.all()) or [strings.Goods.GOOD_NO_CONTROL_CODE]

                if strings.Goods.GOOD_NO_CONTROL_CODE not in new_control_list_entries:
                    new_control_list_entries = [clc.rating for clc in new_control_list_entries]
                else:
                    # Clear flags if control list entries no longer present
                    good.flags.clear()

                if new_control_list_entries != old_control_list_entries:
                    good.flags.clear()
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.GOOD_REVIEWED,
                        action_object=good,
                        target=case,
                        payload={
                            "good_name": good.description,
                            "new_control_list_entry": new_control_list_entries,
                            "old_control_list_entry": old_control_list_entries,
                            "additional_text": data.get("comment"),
                        },
                    )

        apply_good_flagging_rules_for_case(case)

        return JsonResponse(data={}, status=status.HTTP_200_OK)


class GoodList(ListCreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = GoodListSerializer
    pagination_class = GoodListPaginator

    def get_serializer_context(self):
        return {"exporter_user": self.request.user, "organisation_id": get_request_user_organisation_id(self.request)}

    def get_queryset(self):
        description = self.request.GET.get("description", "")
        part_number = self.request.GET.get("part_number", "")
        control_list_entry = self.request.GET.get("control_list_entry")
        for_application = self.request.GET.get("for_application")
        organisation = get_request_user_organisation_id(self.request)

        queryset = Good.objects.filter(
            organisation_id=organisation, description__icontains=description, part_number__icontains=part_number,
        )

        if control_list_entry:
            queryset = queryset.filter(control_list_entries__rating__icontains=control_list_entry).distinct()

        if for_application:
            good_document_ids = GoodDocument.objects.filter(organisation__id=organisation).values_list(
                "good", flat=True
            )
            queryset = queryset.filter(Q(id__in=good_document_ids) | Q(missing_document_reason__isnull=False))

        queryset = queryset.prefetch_related("control_list_entries")

        return queryset.order_by("-updated_at")

    def get_paginated_response(self, data):
        # Get the goods queries for the goods and format in a dict
        ids = [item["id"] for item in data]
        goods_queries = GoodsQuery.objects.filter(good_id__in=ids).values("id", "good_id")
        goods_queries = {str(query["id"]): {"good_id": str(query["good_id"])} for query in goods_queries}

        goods_query_notifications = (
            ExporterNotification.objects.filter(
                user=self.request.user,
                organisation_id=get_request_user_organisation_id(self.request),
                case_id__in=goods_queries.keys(),
            )
            .values("case_id")
            .annotate(count=Count("case_id"))
        )

        # Map goods_query_notifications to goods
        goods_notifications = {}
        for notification in goods_query_notifications:
            case_id = str(notification["case_id"])
            good_id = goods_queries[case_id]["good_id"]
            goods_query_notification_count = notification["count"]
            goods_notifications[good_id] = goods_query_notification_count

        # Set notification counts on each good
        for item in data:
            item["exporter_user_notification_count"] = goods_notifications.get(item["id"], 0)

        return super().get_paginated_response(data)

    def post(self, request, *args, **kwargs):
        """ Add a good to to an organisation. """
        data = request.data
        data["organisation"] = get_request_user_organisation_id(request)
        data["status"] = GoodStatus.DRAFT

        if isinstance(data.get("control_list_entries"), str):
            data["control_list_entries"] = data["control_list_entries"].split(" ")

        item_category = data.get("item_category")
        if item_category:
            # return bad request if trying to edit software_or_technology details outside of category group 3
            if (item_category in ItemCategory.group_one or item_category in ItemCategory.group_two) and data.get(
                "software_or_technology_details"
            ):
                raise BadRequestError({"non_field_errors": [strings.Goods.CANNOT_SET_DETAILS_ERROR]})

            # return bad request if trying to edit component and component details outside of category group 1
            if (item_category in ItemCategory.group_two or item_category in ItemCategory.group_three) and data.get(
                "is_component_step"
            ):
                raise BadRequestError({"non_field_errors": [strings.Goods.CANNOT_SET_DETAILS_ERROR]})

            # return bad request if trying to edit any details that are not applicable to category 2 goods
            if item_category in ItemCategory.group_two:
                check_if_unsupported_fields_edited_on_firearm_good(data)

            # return bad request if adding any of the firearm details on a good that is not in group 2 firearms
            if data.get("firearm_details") and item_category not in ItemCategory.group_two:
                check_if_firearm_details_edited_on_unsupported_good(data)

        serializer = GoodCreateSerializer(data=data)

        return create_or_update_good(serializer, data.get("validate_only"), is_created=True)


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
                    good_data = GoodCreateSerializer(good).data
                else:
                    return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            else:
                good.missing_document_reason = None
                good.save()
                good_data = GoodCreateSerializer(good).data
        else:
            return JsonResponse(
                data={"errors": {"has_document_to_upload": [strings.Goods.DOCUMENT_CHECK_OPTION_NOT_SELECTED]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return JsonResponse(data={"good": good_data}, status=status.HTTP_200_OK)


class GoodTAUDetails(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        good = get_good(pk)

        if isinstance(request.user, ExporterUser):
            if good.organisation.id != get_request_user_organisation_id(request):
                raise PermissionDenied()
            else:
                serializer = TinyGoodDetailsSerializer(good)

        return JsonResponse(data={"good": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """ Edit the TAU details of a good. This includes military use, component and information security use. """
        good = get_good(pk)
        data = request.data.copy()

        # return bad request if trying to edit software_or_technology details outside of category group 3
        if good.item_category in ItemCategory.group_one and "software_or_technology_details" in data:
            raise BadRequestError({"non_field_errors": [strings.Goods.CANNOT_SET_DETAILS_ERROR]})

        # return bad request if trying to edit component and component details outside of category group 1
        if good.item_category in ItemCategory.group_three and data.get("is_component_step"):
            raise BadRequestError({"non_field_errors": [strings.Goods.CANNOT_SET_DETAILS_ERROR]})

        # return bad request if editing any of the firearm details on a good that is not in group 2 firearms
        if good.item_category not in ItemCategory.group_two and data.get("firearm_details"):
            check_if_firearm_details_edited_on_unsupported_good(data)

        # return bad request if trying to edit any details that are not applicable to category 2 firearm goods
        if good.item_category in ItemCategory.group_two:
            check_if_unsupported_fields_edited_on_firearm_good(data)

        if good.status == GoodStatus.SUBMITTED:
            raise BadRequestError({"non_field_errors": [strings.Goods.CANNOT_EDIT_GOOD]})

        serializer = GoodCreateSerializer(instance=good, data=data, partial=True)
        return create_or_update_good(serializer, data.get("validate_only"), is_created=False)


class GoodOverview(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        good = get_good(pk)

        if isinstance(request.user, ExporterUser):
            if good.organisation.id != get_request_user_organisation_id(request):
                raise PermissionDenied()

            if str_to_bool(request.GET.get("full_detail")):
                serializer = GoodSerializerExporterFullDetail(
                    good,
                    context={
                        "exporter_user": request.user,
                        "organisation_id": get_request_user_organisation_id(request),
                    },
                )
            else:
                serializer = GoodSerializerExporter(good)

            # If there's a query with this good, update the notifications on it
            query = GoodsQuery.objects.filter(good=good)
            if query:
                delete_exporter_notifications(
                    user=request.user, organisation_id=get_request_user_organisation_id(request), objects=query
                )
        else:
            serializer = GoodSerializerInternal(good)

        return JsonResponse(data={"good": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """ Edit details of a good. This includes description, control codes and PV grading. """
        good = get_good(pk)

        if good.organisation.id != get_request_user_organisation_id(request):
            raise PermissionDenied()

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()

        if (
            data.get("is_good_controlled") == GoodControlled.UNSURE
            or data.get("is_pv_graded") == GoodPvGraded.GRADING_REQUIRED
        ):
            for good_on_application in GoodOnApplication.objects.filter(good=good):
                good_on_application.delete()

        data["organisation"] = get_request_user_organisation_id(request)

        serializer = GoodCreateSerializer(instance=good, data=data, partial=True)
        return create_or_update_good(serializer, data.get("validate_only"), is_created=False)

    def delete(self, request, pk):
        good = get_good(pk)

        if good.organisation.id != get_request_user_organisation_id(request):
            raise PermissionDenied()

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
        good_documents = GoodDocument.objects.filter(good_id=pk).order_by("-created_at")
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

        if good.organisation.id != get_request_user_organisation_id(request):
            delete_documents_on_bad_request(data)
            raise PermissionDenied()

        if good.status != GoodStatus.DRAFT:
            delete_documents_on_bad_request(data)
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        for document in data:
            document["good"] = good_id
            document["user"] = request.user.id
            document["organisation"] = get_request_user_organisation_id(request)

        serializer = GoodDocumentCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            try:
                serializer.save()
            except Exception as e:  # noqa
                return JsonResponse(
                    {"errors": {"file": strings.Documents.UPLOAD_FAILURE}}, status=status.HTTP_400_BAD_REQUEST
                )
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

        if good.organisation.id != get_request_user_organisation_id(request):
            raise PermissionDenied()

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

        if good.organisation.id != get_request_user_organisation_id(request):
            raise PermissionDenied()

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
