from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView

from api.applications.helpers import delete_uploaded_document
from api.applications.libraries.case_status_helpers import get_case_statuses
from api.applications.libraries.get_applications import get_application
from api.applications.models import BaseApplication, GoodOnApplication, GoodOnApplicationDocument, StandardApplication
from api.applications.serializers.good import (
    GoodOnApplicationViewSerializer,
    GoodOnApplicationCreateSerializer,
    GoodOnApplicationDocumentViewSerializer,
    GoodOnApplicationDocumentCreateSerializer,
    GoodOnApplicationUpdateSerializer,
)
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enums import CaseTypeReferenceEnum
from api.cases.models import Case
from api.core.authentication import ExporterAuthentication, GovAuthentication, SharedAuthentication
from api.core.decorators import (
    authorised_to_view_application,
    allowed_application_types,
    application_is_major_editable,
)
from api.core.exceptions import BadRequestError
from api.flags.enums import SystemFlags
from api.goods.enums import GoodStatus
from api.goods.helpers import FIREARMS_CORE_TYPES, get_rfd_status
from api.goods.libraries.get_goods import get_good_with_organisation
from api.goods.serializers import FirearmDetailsSerializer
from lite_content.lite_api import strings
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.models import ExporterUser


class ApplicationGoodsOnApplication(APIView):
    """
    Goods belonging to a standard application
    """

    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [
            CaseTypeReferenceEnum.EXPORT_LICENCE,
            CaseTypeReferenceEnum.SIEL,
            CaseTypeReferenceEnum.F680,
        ]
    )
    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk):
        goods = GoodOnApplication.objects.filter(application_id=pk)
        goods_data = GoodOnApplicationViewSerializer(goods, many=True).data

        return JsonResponse(data={"goods": goods_data})

    @allowed_application_types(
        [
            CaseTypeReferenceEnum.EXPORT_LICENCE,
            CaseTypeReferenceEnum.SIEL,
            CaseTypeReferenceEnum.F680,
        ]
    )
    @application_is_major_editable
    @authorised_to_view_application(ExporterUser)
    def post(self, request, pk):
        data = request.data
        data["application"] = pk
        rfd_status = False

        if "validate_only" in data and not isinstance(data["validate_only"], bool):
            return JsonResponse(
                data={"error": strings.Goods.VALIDATE_ONLY_ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "validate_only" in data and data["validate_only"] is True:
            # validate the value, quantity, and units relating to a good on an application.
            # note: Goods attached to applications also need documents. This is validated at a later stage.
            serializer = GoodOnApplicationCreateSerializer(data=data, partial=True)
            if serializer.is_valid():
                return JsonResponse(status=status.HTTP_200_OK, data={})
        else:
            if "good_id" not in data:
                return JsonResponse(
                    data={"error": strings.Goods.GOOD_ID_ERROR},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data["good"] = data["good_id"]

            good = get_good_with_organisation(data.get("good"), get_request_user_organisation_id(request))

            if data.get("firearm_details") and good.firearm_details.type in FIREARMS_CORE_TYPES:
                rfd_status = get_rfd_status(data, good.organisation_id)

                data["firearm_details"]["rfd_status"] = rfd_status

                # If the user is a registered firearms dealer and has a valid certificate then it
                # covers section1 and section2 so in this case if the answer is Yes to firearms act question
                # then it implicitly means it is for section5
                if (
                    rfd_status
                    and data["firearm_details"].get("is_covered_by_firearm_act_section_one_two_or_five") == "Yes"
                ):
                    data["firearm_details"]["firearms_act_section"] = "firearms_act_section5"

            serializer = GoodOnApplicationCreateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()

                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ADD_GOOD_TO_APPLICATION,
                    action_object=good,
                    target=Case.objects.get(id=pk),
                    payload={"good_name": good.name or good.description},
                )

                return JsonResponse(data={"good": serializer.data}, status=status.HTTP_201_CREATED)

        errors = {**serializer.errors}
        if rfd_status and "is_covered_by_firearm_act_section_one_two_or_five" in serializer.errors:
            errors["is_covered_by_firearm_act_section_one_two_or_five"] = [
                "Select yes if the product is covered by section 5 of the Firearms Act 1968"
            ]

        return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)


class ApplicationGoodOnApplication(APIView):
    """Good on a standard application."""

    authentication_classes = (SharedAuthentication,)
    serializer_class = GoodOnApplicationViewSerializer

    def get_object(self):
        return get_object_or_404(GoodOnApplication.objects.all(), pk=self.kwargs["obj_pk"])

    def get(self, request, **kwargs):
        good_on_application = self.get_object()
        serializer = self.serializer_class(good_on_application, context={"include_audit_trail": True})
        return JsonResponse(serializer.data)

    def put(self, request, **kwargs):
        good_on_application = self.get_object()

        application = good_on_application.application

        if application.status.status in get_case_statuses(read_only=True):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.READ_ONLY]},
                status=status.HTTP_403_FORBIDDEN,
            )

        if good_on_application.application.organisation.id != get_request_user_organisation_id(request):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.INVALID_ORGANISATION]},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data.copy()
        serializer = self.serializer_class(instance=good_on_application, data=data, partial=True)
        if not serializer.is_valid():
            return JsonResponse(
                data={"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        return JsonResponse(status=status.HTTP_200_OK, data=serializer.data)

    def delete(self, request, obj_pk):
        good_on_application = self.get_object()
        application = good_on_application.application

        if application.status.status in get_case_statuses(read_only=True):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.READ_ONLY]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if good_on_application.application.organisation.id != get_request_user_organisation_id(request):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.INVALID_ORGANISATION]},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            good_on_application.good.status == GoodStatus.SUBMITTED
            and GoodOnApplication.objects.filter(good=good_on_application.good).count() == 1
        ):
            good_on_application.good.status = GoodStatus.DRAFT
            good_on_application.good.save()

        good_on_application.delete()

        # if the application no longer has goods with firearm details, remove the flag
        if (
            not application.goods.filter(good__firearm_details__isnull=False).exists()
            and application.flags.filter(id=SystemFlags.FIREARMS_ID).exists()
        ):
            application.flags.remove(SystemFlags.FIREARMS_ID)

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.REMOVE_GOOD_FROM_APPLICATION,
            action_object=good_on_application.good,
            target=application.get_case(),
            payload={"good_name": good_on_application.good.name or good_on_application.good.description},
        )

        return JsonResponse(data={"status": "success"}, status=status.HTTP_200_OK)


class ApplicationGoodOnApplicationUpdateViewInternal(APIView):
    """View to update GoodOnApplication by Internal users"""

    authentication_classes = (GovAuthentication,)
    serializer_class = GoodOnApplicationUpdateSerializer

    def get_application(self):
        return get_object_or_404(StandardApplication.objects.all(), pk=self.kwargs["pk"])

    def put(self, request, **kwargs):
        application = self.get_application()
        if CaseStatusEnum.is_terminal(application.status.status):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.READ_ONLY]},
                status=status.HTTP_403_FORBIDDEN,
            )

        good_on_application_ids = [item["id"] for item in request.data]
        serializer = self.serializer_class(
            GoodOnApplication.objects.filter(id__in=good_on_application_ids),
            data=request.data,
            partial=True,
            many=True,
        )
        if not serializer.is_valid():
            return JsonResponse(
                data={"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()

        return JsonResponse(status=status.HTTP_200_OK, data={"data": serializer.data})


class ApplicationGoodOnApplicationDocumentView(APIView):
    authentication_classes = (SharedAuthentication,)

    def get_object(self):
        return get_object_or_404(BaseApplication.objects.all(), pk=self.kwargs["pk"])

    # @authorised_to_view_application(ExporterUser)
    def get(self, request, pk, good_pk):
        documents = GoodOnApplicationDocument.objects.filter(application_id=pk, good_id=good_pk).order_by("-created_at")
        include_unsafe = request.GET.get("include_unsafe", False)
        if not include_unsafe:
            documents = documents.filter(safe=True)

        serializer = GoodOnApplicationDocumentViewSerializer(documents, many=True)

        return JsonResponse({"documents": serializer.data}, status=status.HTTP_200_OK)

    @application_is_major_editable
    @authorised_to_view_application(ExporterUser)
    def post(self, request, pk, good_pk):
        data = request.data
        application = self.get_object()

        if application.status.status in get_case_statuses(read_only=True):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.READ_ONLY]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data["good"] = good_pk
        data["application"] = pk
        data["user"] = request.user.pk

        serializer = GoodOnApplicationDocumentCreateSerializer(data=data)
        if serializer.is_valid():
            try:
                serializer.save()
            except Exception:
                return JsonResponse(
                    {"errors": {"file": strings.Documents.UPLOAD_FAILURE}}, status=status.HTTP_400_BAD_REQUEST
                )
            return JsonResponse({"documents": serializer.data}, status=status.HTTP_201_CREATED)

        delete_uploaded_document(data)
        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @application_is_major_editable
    @authorised_to_view_application(ExporterUser)
    def delete(self, request, pk, good_pk):
        delete_uploaded_document(request.data)
        return JsonResponse({}, status=status.HTTP_200_OK)


class ApplicationGoodOnApplicationDocumentDetailView(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, **kwargs):
        document = get_object_or_404(GoodOnApplicationDocument.objects.all(), pk=self.kwargs["doc_pk"])
        serializer = GoodOnApplicationDocumentViewSerializer(document)
        return JsonResponse({"document": serializer.data})

    @transaction.atomic
    def delete(self, request, **kwargs):
        document = get_object_or_404(GoodOnApplicationDocument.objects.all(), pk=kwargs["doc_pk"])
        if document.good.status != GoodStatus.DRAFT:
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"}, status=status.HTTP_400_BAD_REQUEST
            )

        document.delete_s3()
        document.delete()

        return JsonResponse({"document": "deleted success"})


class ApplicationGoodOnApplicationUpdateSerialNumbers(APIView):
    authentication_classes = (SharedAuthentication,)

    def put(self, request, pk, good_on_application_pk):
        application = get_application(pk)

        if application.status.status not in [
            CaseStatusEnum.SUBMITTED,
            CaseStatusEnum.FINALISED,
        ]:
            raise BadRequestError({"non_field_errors": ["Incorrect application status"]})

        good_on_application = GoodOnApplication.objects.get(pk=good_on_application_pk)

        data = request.data.copy()

        serializer = FirearmDetailsSerializer(
            instance=good_on_application.firearm_details,
            data=data,
            partial=True,
        )
        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.UPDATED_SERIAL_NUMBERS,
            target=application.get_case(),
            payload={
                "good_name": good_on_application.good.name,
            },
            ignore_case_status=True,
        )

        return JsonResponse(
            {
                "serial_numbers": serializer.validated_data["serial_numbers"],
            },
            status=status.HTTP_200_OK,
        )
