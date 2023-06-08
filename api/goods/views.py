import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils.functional import cached_property
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.views import APIView

from api.applications.models import (
    GoodOnApplication,
    BaseApplication,
    GoodOnApplicationInternalDocument,
    StandardApplication,
)
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enums import CaseTypeSubTypeEnum
from api.cases.libraries.delete_notifications import delete_exporter_notifications
from api.cases.libraries.get_case import get_case
from api.core import constants
from api.core.authentication import ExporterAuthentication, SharedAuthentication, GovAuthentication
from api.core.exceptions import BadRequestError
from api.core.helpers import str_to_bool
from api.core.permissions import assert_user_has_permission
from api.documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from api.documents.models import Document
from api.flags.enums import SystemFlags
from api.goods.enums import GoodStatus, GoodPvGraded, ItemCategory
from api.goods.goods_paginator import GoodListPaginator
from api.goods.helpers import (
    FIREARMS_CORE_TYPES,
    check_if_firearm_details_edited_on_unsupported_good,
    get_rfd_status,
    has_valid_certificate,
)
from api.goods.libraries.get_goods import get_good, get_good_document
from api.goods.libraries.save_good import create_or_update_good
from api.goods.models import Good, GoodDocument
from api.goods.serializers import (
    GoodAttachingSerializer,
    GoodCreateSerializer,
    GoodDocumentViewSerializer,
    GoodDocumentCreateSerializer,
    ControlGoodOnApplicationSerializer,
    GoodListSerializer,
    GoodSerializerInternal,
    GoodSerializerExporter,
    GoodSerializerExporterFullDetail,
    GoodDocumentAvailabilitySerializer,
    GoodDocumentSensitivitySerializer,
    TinyGoodDetailsSerializer,
)
from api.applications.serializers.good import (
    GoodOnApplicationInternalDocumentCreateSerializer,
    GoodOnApplicationInternalDocumentViewSerializer,
)

from api.goodstype.models import GoodsType
from api.goodstype.serializers import ClcControlGoodTypeSerializer
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from lite_content.lite_api import strings
from api.organisations.models import OrganisationDocumentType
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.queries.goods_query.models import GoodsQuery
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.models import ExporterNotification

good_overview_put_deletion_logger = logging.getLogger(settings.GOOD_OVERVIEW_PUT_DELETION_LOGGER)

GOOD_ON_APP_BAD_REPORT_SUMMARY_PREFIX = "Select a valid report summary prefix"
GOOD_ON_APP_BAD_REPORT_SUMMARY_SUBJECT = "Select a valid report summary subject"


def get_new_report_summary_data(request):
    data = request.data
    summary = data.get("report_summary")
    rs_subject, rs_prefix = None, None

    subject_id = data.get("report_summary_subject")
    if subject_id:
        try:
            rs_subject = ReportSummarySubject.objects.get(id=subject_id)
        except ReportSummarySubject.DoesNotExist:
            raise ValidationError(GOOD_ON_APP_BAD_REPORT_SUMMARY_SUBJECT)
        summary = rs_subject.name

    prefix_id = data.get("report_summary_prefix")
    if prefix_id:
        try:
            rs_prefix = ReportSummaryPrefix.objects.get(id=prefix_id)
        except ReportSummaryPrefix.DoesNotExist:
            raise ValidationError(GOOD_ON_APP_BAD_REPORT_SUMMARY_PREFIX)

    if rs_subject is None and rs_prefix is not None:
        raise ValidationError(GOOD_ON_APP_BAD_REPORT_SUMMARY_SUBJECT)

    if rs_subject is not None and rs_prefix is not None:
        summary = f"{rs_prefix.name} {rs_subject.name}"

    return summary


class GoodsListControlCode(APIView):
    authentication_classes = (GovAuthentication,)

    @cached_property
    def application(self):
        return BaseApplication.objects.select_related("status").get(id=self.kwargs["case_pk"])

    def get_queryset(self):
        pks = self.request.data["objects"]
        if not isinstance(pks, list):
            pks = [pks]
        if self.application.case_type.sub_type in [CaseTypeSubTypeEnum.OPEN, CaseTypeSubTypeEnum.HMRC]:
            return GoodsType.objects.filter(pk__in=pks)
        return GoodOnApplication.objects.filter(application_id=self.kwargs["case_pk"], good_id__in=pks)

    def get_serializer_class(self):
        if self.application.case_type.sub_type in [CaseTypeSubTypeEnum.OPEN, CaseTypeSubTypeEnum.HMRC]:
            return ClcControlGoodTypeSerializer
        return ControlGoodOnApplicationSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        return serializer_class(*args, **kwargs, data=self.request.data)

    def check_permissions(self, request):
        assert_user_has_permission(request.user.govuser, constants.GovPermissions.REVIEW_GOODS)

    def get_application_line_items(self, case):
        line_items = {}
        application = StandardApplication.objects.get(id=case.id)
        good_on_application_qs = self.get_queryset()
        good_on_application_ids = [g.id for g in application.goods.all()]

        for item in good_on_application_qs:
            line_items[item.id] = good_on_application_ids.index(item.id)

        return line_items

    @transaction.atomic
    def post(self, request, case_pk):
        if CaseStatusEnum.is_terminal(self.application.status.status):
            return JsonResponse(
                data={"errors": {"error": [strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_report_summary = get_new_report_summary_data(request)
        except ValidationError as ex:
            return JsonResponse(
                data={"errors": {"error": [ex.message]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.data["report_summary"] = new_report_summary

        case = get_case(case_pk)
        line_items = self.get_application_line_items(case)

        for good in self.get_queryset():
            data = request.data.copy()

            old_report_summary = good.report_summary
            old_control_list_entries = list(good.control_list_entries.values_list("rating", flat=True))
            old_is_controlled = good.is_good_controlled
            old_regime_entries = list(good.regime_entries.values_list("name", flat=True))

            report_summary_updated = new_report_summary != old_report_summary

            if report_summary_updated and str(good.id) != data.get("current_object", str(good.id)):
                data["report_summary"] = good.report_summary

            serializer_class = self.get_serializer_class()
            serializer = serializer_class(good, data=data)
            serializer.is_valid(raise_exception=True)
            obj = serializer.save()

            if "control_list_entries" in serializer.data or "is_good_controlled" in serializer.data:
                new_control_list_entries = [item.rating for item in serializer.validated_data["control_list_entries"]]
                new_is_controlled = serializer.validated_data["is_good_controlled"]
                new_regime_entries = [
                    regime_entry.name for regime_entry in serializer.validated_data.get("regime_entries", [])
                ]

                if (
                    new_control_list_entries != old_control_list_entries
                    or new_is_controlled != old_is_controlled
                    or report_summary_updated
                ):
                    default_control = [strings.Goods.GOOD_NO_CONTROL_CODE]
                    default_regimes = ["No regimes"]

                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.PRODUCT_REVIEWED,
                        action_object=good,
                        target=case,
                        payload={
                            "line_no": line_items[good.id] + 1,
                            "good_name": good.name,
                            "new_control_list_entry": new_control_list_entries or default_control,
                            "old_control_list_entry": old_control_list_entries or default_control,
                            "old_is_good_controlled": "Yes" if old_is_controlled else "No",
                            "new_is_good_controlled": "Yes" if new_is_controlled else "No",
                            "old_report_summary": old_report_summary,
                            "report_summary": new_report_summary,
                            "additional_text": serializer.validated_data["comment"],
                            "is_precedent": serializer.validated_data.get("is_precedent", False),
                            "old_regime_entries": old_regime_entries or default_regimes,
                            "new_regime_entries": new_regime_entries or default_regimes,
                        },
                    )

            # Add or remove WASSENAAR flag based on whether the user chose to apply it
            good = obj.good
            if serializer.validated_data.get("is_wassenaar"):
                good.flags.add(SystemFlags.WASSENAAR)
            else:
                good.flags.remove(SystemFlags.WASSENAAR)

        return JsonResponse(data={}, status=status.HTTP_200_OK)


class GoodList(ListCreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = GoodListSerializer
    pagination_class = GoodListPaginator

    def get_serializer_context(self):
        return {
            "exporter_user": self.request.user.exporteruser,
            "organisation_id": get_request_user_organisation_id(self.request),
        }

    def get_queryset(self):
        name = self.request.GET.get("name", "")
        description = self.request.GET.get("description", "")
        part_number = self.request.GET.get("part_number", "")
        control_list_entry = self.request.GET.get("control_list_entry")
        for_application = self.request.GET.get("for_application")
        organisation = get_request_user_organisation_id(self.request)

        queryset = Good.objects.filter(
            organisation_id=organisation,
            name__icontains=name,
            description__icontains=description,
            part_number__icontains=part_number,
        )

        if control_list_entry:
            queryset = queryset.filter(control_list_entries__rating__icontains=control_list_entry).distinct()

        if for_application:
            good_document_ids = GoodDocument.objects.filter(organisation__id=organisation).values_list(
                "good", flat=True
            )
            queryset = queryset.filter(Q(id__in=good_document_ids) | Q(is_document_available__isnull=False))

        queryset = queryset.prefetch_related("control_list_entries")

        return queryset.order_by("-updated_at")

    def get_paginated_response(self, data):
        # Get the goods queries for the goods and format in a dict
        ids = [item["id"] for item in data]
        goods_queries = GoodsQuery.objects.filter(good_id__in=ids).values("id", "good_id")
        goods_queries = {str(query["id"]): {"good_id": str(query["good_id"])} for query in goods_queries}

        goods_query_notifications = (
            ExporterNotification.objects.filter(
                user_id=self.request.user.pk,
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
        """Add a good to to an organisation."""
        data = request.data
        data["organisation"] = get_request_user_organisation_id(request)
        data["status"] = GoodStatus.DRAFT

        if isinstance(data.get("control_list_entries"), str):
            data["control_list_entries"] = data["control_list_entries"].split(" ")

        item_category = data.get("item_category")
        if item_category:
            # return bad request if trying to edit software_or_technology details outside of category group 3
            if (item_category in ItemCategory.group_one) and data.get("software_or_technology_details"):
                raise BadRequestError({"non_field_errors": [strings.Goods.CANNOT_SET_DETAILS_ERROR]})

            # return bad request if adding any of the firearm details on a good that is not in group 2 firearms
            if data.get("firearm_details") and item_category not in ItemCategory.group_two:
                check_if_firearm_details_edited_on_unsupported_good(data)

            # check if the user is registered firearm dealer
            if item_category == ItemCategory.GROUP2_FIREARMS:
                if data.get("firearm_details") and data["firearm_details"]["type"] in FIREARMS_CORE_TYPES:
                    rfd_status = get_rfd_status(data, str(data["organisation"]))

                    data["firearm_details"]["rfd_status"] = rfd_status

                    # If the user is a registered firearms dealer and has a valid certificate then it
                    # covers section1 and section2 so in this case if the answer is Yes to firearms act question
                    # then it implicitly means it is for section5
                    if (
                        rfd_status
                        and data["firearm_details"].get("is_covered_by_firearm_act_section_one_two_or_five") == "Yes"
                    ):
                        data["firearm_details"]["firearms_act_section"] = "firearms_act_section5"

        serializer = GoodCreateSerializer(data=data)

        return create_or_update_good(serializer, data, is_created=True)


class GoodDocumentAvailabilityCheck(APIView):
    """
    Check document is attached to application good/product
    """

    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        good = get_good(pk)
        good_data = GoodDocumentAvailabilitySerializer(instance=good).data
        return JsonResponse(data={"good": good_data}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        good = get_good(pk)
        data = request.data
        if data.get("is_document_available"):
            good.is_document_available = str_to_bool(data["is_document_available"])

            # If no document is attached, then we require reasoning comments from exporter
            if not good.is_document_available and not data.get("no_document_comments"):
                return JsonResponse(
                    data={
                        "errors": {"no_document_comments": ["Enter a reason why you cannot upload a product document"]}
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # TODO: Poor implementation? Is there a reason we don't use the serialized data? Add comment or fix this.
            good.no_document_comments = data.get("no_document_comments", "")
            good.save()
            good_data = GoodCreateSerializer(good).data
            return JsonResponse(data={"good": good_data}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(
                data={"errors": {"is_document_available": ["Select yes or no"]}}, status=status.HTTP_400_BAD_REQUEST
            )


class GoodDocumentCriteriaCheck(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        good = get_good(pk)
        serializer = GoodDocumentSensitivitySerializer(instance=good)
        return JsonResponse(data={"good": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        good = get_good(pk)
        data = request.data
        if data.get("is_document_sensitive"):
            good.is_document_sensitive = str_to_bool(data["is_document_sensitive"])
            good.save()
            serializer = GoodCreateSerializer(good)
            return JsonResponse(data={"good": serializer.data}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(
                data={"errors": {"is_document_sensitive": ["Select yes or no"]}}, status=status.HTTP_400_BAD_REQUEST
            )


class GoodTAUDetails(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        good = get_good(pk)

        if hasattr(request.user, "exporteruser"):
            if good.organisation_id != get_request_user_organisation_id(request):
                raise PermissionDenied()
            else:
                serializer = TinyGoodDetailsSerializer(good)

        return JsonResponse(data={"good": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Edit the TAU details of a good. This includes military use, component and information security use."""
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

        if good.status == GoodStatus.SUBMITTED:
            raise BadRequestError({"non_field_errors": [strings.Goods.CANNOT_EDIT_GOOD]})

        # check if the user is registered firearm dealer
        if good.item_category == ItemCategory.GROUP2_FIREARMS and good.firearm_details.type in FIREARMS_CORE_TYPES:
            is_rfd = has_valid_certificate(
                good.organisation_id, OrganisationDocumentType.REGISTERED_FIREARM_DEALER_CERTIFICATE
            )
            data["firearm_details"]["rfd_status"] = is_rfd

            # If the user is a registered firearms dealer and has a valid certificate then it
            # covers section1 and section2 so in this case if the answer is Yes to firearms act question
            # then it implicitly means it is for section5
            if is_rfd and data["firearm_details"].get("is_covered_by_firearm_act_section_one_two_or_five") == "Yes":
                data["firearm_details"]["firearms_act_section"] = "firearms_act_section5"

        serializer = GoodCreateSerializer(instance=good, data=data, partial=True)
        return create_or_update_good(serializer, data, is_created=False)


class GoodOverview(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        good = get_good(pk)

        if hasattr(request.user, "exporteruser"):
            if good.organisation_id != get_request_user_organisation_id(request):
                raise PermissionDenied()

            if str_to_bool(request.GET.get("full_detail")):
                serializer = GoodSerializerExporterFullDetail(
                    good,
                    context={
                        "exporter_user": request.user.exporteruser,
                        "organisation_id": get_request_user_organisation_id(request),
                    },
                )
            else:
                serializer = GoodSerializerExporter(good)

            # If there's a query with this good, update the notifications on it
            query = GoodsQuery.objects.filter(good=good)
            if query.exists():
                delete_exporter_notifications(
                    user=request.user.exporteruser,
                    organisation_id=get_request_user_organisation_id(request),
                    objects=query,
                )
        else:
            serializer = GoodSerializerInternal(good)

        return JsonResponse(data={"good": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Edit details of a good. This includes description, control codes and PV grading."""
        good = get_good(pk)

        if good.organisation_id != get_request_user_organisation_id(request):
            raise PermissionDenied()

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()

        if data.get("is_good_controlled") is None or data.get("is_pv_graded") == GoodPvGraded.GRADING_REQUIRED:
            good_overview_put_deletion_logger.warning(
                "Code removed: we would have just deleted GoodOnApplication for good id: %s sending data: %s",
                good.id,
                data,
            )

        data["organisation"] = get_request_user_organisation_id(request)

        serializer = GoodCreateSerializer(instance=good, data=data, partial=True)
        return create_or_update_good(serializer, data, is_created=False)

    def delete(self, request, pk):
        good = get_good(pk)

        if good.organisation_id != get_request_user_organisation_id(request):
            raise PermissionDenied()

        if good.status != GoodStatus.DRAFT:
            return JsonResponse(
                data={"errors": "Good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        for document in GoodDocument.objects.filter(good=good):
            document.delete_s3()

        good.delete()
        return JsonResponse(data={"status": "Good Deleted"}, status=status.HTTP_200_OK)


class GoodAttaching(APIView):
    authentication_classes = (SharedAuthentication,)

    def put(self, request, pk):
        """Edit details of a good for attaching.

        This is distinct from normal editing of a good as we allow this to be
        edited regardless of the application status unlike `GoodOverview`.

        For safety we only allow a subset of fields to be edited.
        """
        good = get_good(pk)

        if good.organisation_id != get_request_user_organisation_id(request):
            raise PermissionDenied()

        data = request.data.copy()

        serializer = GoodAttachingSerializer(instance=good, data=data, partial=True)
        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return JsonResponse(
            data={"good": serializer.data},
            status=status.HTTP_200_OK,
        )


class GoodDocuments(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns a list of documents on the specified good
        """
        good_documents = GoodDocument.objects.filter(good_id=pk).order_by("-created_at")
        serializer = GoodDocumentViewSerializer(good_documents, many=True)

        return JsonResponse({"documents": serializer.data})

    @transaction.atomic
    def post(self, request, pk):
        """
        Adds a document to the specified good
        """
        good = get_good(pk)
        good_id = str(good.id)
        data = request.data

        if good.organisation_id != get_request_user_organisation_id(request):
            delete_documents_on_bad_request(data)
            raise PermissionDenied()

        if good.status != GoodStatus.DRAFT:
            delete_documents_on_bad_request(data)
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        for document in data:
            document["good"] = good_id
            document["user"] = request.user.pk
            document["organisation"] = get_request_user_organisation_id(request)

        serializer = GoodDocumentCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            try:
                serializer.save()
            except Exception as e:  # noqa
                return JsonResponse(
                    {"errors": {"file": strings.Documents.UPLOAD_FAILURE}}, status=status.HTTP_400_BAD_REQUEST
                )
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

        if good.organisation_id != get_request_user_organisation_id(request):
            raise PermissionDenied()

        if good.status != GoodStatus.DRAFT:
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        good_document = get_good_document(good, doc_pk)
        serializer = GoodDocumentViewSerializer(good_document)
        return JsonResponse({"document": serializer.data})

    @transaction.atomic
    def put(self, request, pk, doc_pk):
        good = get_good(pk)

        if good.organisation_id != get_request_user_organisation_id(request):
            raise PermissionDenied()

        if good.status != GoodStatus.DRAFT:
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        document = Document.objects.get(id=doc_pk)
        good_document = get_good_document(good, document.id)
        serializer = GoodDocumentCreateSerializer(instance=good_document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({"document": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def delete(self, request, pk, doc_pk):
        """
        Deletes good document
        """
        good = get_good(pk)

        if good.organisation_id != get_request_user_organisation_id(request):
            raise PermissionDenied()

        if good.status != GoodStatus.DRAFT:
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        good_document = Document.objects.get(id=doc_pk)
        document = get_good_document(good, good_document.id)
        document.delete_s3()

        good_document.delete()
        if not GoodDocument.objects.filter(good=good).exists():
            for good_on_application in GoodOnApplication.objects.filter(good=good):
                good_on_application.delete()

        return JsonResponse({"document": "deleted success"})


class DocumentGoodOnApplicationInternalView(APIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = GoodOnApplicationInternalDocumentCreateSerializer

    def post(self, request, goods_on_application_pk):
        data = request.data
        data["good_on_application"] = goods_on_application_pk
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse({"document": serializer.data}, status=201)

        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class DocumentGoodOnApplicationInternalDetailView(APIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = GoodOnApplicationInternalDocumentViewSerializer

    def get(self, request, doc_pk):
        document = get_object_or_404(GoodOnApplicationInternalDocument.objects.all(), pk=doc_pk)
        serializer = self.serializer_class(document)
        return JsonResponse({"document": serializer.data})

    def put(self, request, doc_pk):
        document = GoodOnApplicationInternalDocument.objects.get(id=doc_pk)
        serializer = GoodOnApplicationInternalDocumentCreateSerializer(
            instance=document, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({"document": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, doc_pk):
        document = GoodOnApplicationInternalDocument.objects.get(id=doc_pk)
        document.delete_s3()
        document.delete()
        return JsonResponse(data={"internal good on application document": "Deleted"}, status=status.HTTP_200_OK)
