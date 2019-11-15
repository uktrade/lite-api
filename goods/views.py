from django.db import transaction
from django.http import JsonResponse, Http404, HttpResponse
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from cases.libraries.activity_types import CaseActivityType
from cases.libraries.get_case import get_case
from cases.models import CaseActivity
from conf.authentication import (
    ExporterAuthentication,
    SharedAuthentication,
    GovAuthentication,
)
from conf.constants import Permissions
from conf.permissions import assert_user_has_permission
from documents.libraries.delete_documents_on_bad_request import (
    delete_documents_on_bad_request,
)
from documents.models import Document
from applications.models import GoodOnApplication
from goods.enums import GoodStatus
from goods.libraries.get_goods import get_good, get_good_document
from goods.models import Good, GoodDocument
from goods.serializers import (
    GoodSerializer,
    GoodDocumentViewSerializer,
    GoodDocumentCreateSerializer,
    ClcControlGoodSerializer,
    GoodListSerializer,
    GoodWithFlagsSerializer,
)
from queries.control_list_classifications.models import ControlListClassificationQuery
from users.models import ExporterUser


class GoodsListControlCode(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def post(self, request, case_pk):
        """
        Set control list codes on multiple goods.
        """
        assert_user_has_permission(request.user, Permissions.REVIEW_GOODS)

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
                    serializer = ClcControlGoodSerializer(good, data=data)
                    if serializer.is_valid():
                        serializer.save()

                    control_code = data.get("control_code")
                    if control_code == "":
                        control_code = "No control code"

                    # Add an activity item for the query's case
                    CaseActivity.create(
                        activity_type=CaseActivityType.GOOD_REVIEWED,
                        good_name=good.description,
                        control_code=control_code,
                        case=case,
                        user=request.user,
                    )

                except Http404:
                    error_occurred = True

            if not error_occurred:
                return HttpResponse(status=status.HTTP_200_OK)
            else:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse(
                data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )


class GoodList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        Returns a list of all goods belonging to an organisation
        """
        description = request.GET.get("description", "")
        part_number = request.GET.get("part_number", "")
        control_rating = request.GET.get("control_rating", "")
        goods = Good.objects.filter(
            organisation_id=request.user.organisation.id,
            description__icontains=description,
            part_number__icontains=part_number,
            control_code__icontains=control_rating,
        ).order_by("description")
        serializer = GoodListSerializer(goods, many=True)
        return JsonResponse(data={"goods": serializer.data})

    def post(self, request):
        """
        Add a good to to an organisation
        """
        data = request.data
        data["organisation"] = request.user.organisation.id
        data["status"] = GoodStatus.DRAFT
        serializer = GoodSerializer(data=data)

        if not serializer.is_valid():
            return JsonResponse(
                data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        if "validate_only" in data and data["validate_only"] is True:
            return HttpResponse(status=status.HTTP_200_OK)
        else:
            serializer.save()

            return JsonResponse(
                data={"good": serializer.data}, status=status.HTTP_201_CREATED
            )


class GoodDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        good = get_good(pk)

        if isinstance(request.user, ExporterUser):
            if good.organisation != request.user.organisation:
                raise Http404

            serializer = GoodSerializer(good)

            # If there's a query with this good, update the notifications on it
            try:
                query = ControlListClassificationQuery.objects.get(good=good)
                request.user.notification_set.filter(
                    case_note__case__query=query
                ).update(viewed_at=timezone.now())
                request.user.notification_set.filter(query=query.id).update(
                    viewed_at=timezone.now()
                )
            except ControlListClassificationQuery.DoesNotExist:
                pass
        else:
            serializer = GoodWithFlagsSerializer(good)

        return JsonResponse(data={"good": serializer.data})

    def put(self, request, pk):
        good = get_good(pk)

        if good.organisation != request.user.organisation:
            raise Http404

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(
                data={"errors": "This good is already on a submitted application"},
                status=status.HTTP_400_BAD_REQUEST,
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
        return JsonResponse(
            data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        good = get_good(pk)

        if good.organisation != request.user.organisation:
            raise Http404

        if good.status != GoodStatus.DRAFT:
            return JsonResponse(
                data={"errors": "Good is already on a submitted application"},
                status=status.HTTP_400_BAD_REQUEST,
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

    @swagger_auto_schema(
        request_body=GoodDocumentCreateSerializer, responses={400: "JSON parse error"}
    )
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
                data={"errors": "This good is already on a submitted application"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for document in data:
            document["good"] = good_id
            document["user"] = request.user.id
            document["organisation"] = request.user.organisation.id

        serializer = GoodDocumentCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(
                {"documents": serializer.data}, status=status.HTTP_201_CREATED
            )

        delete_documents_on_bad_request(data)
        return JsonResponse(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )


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
                data={"errors": "This good is already on a submitted application"},
                status=status.HTTP_400_BAD_REQUEST,
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
                data={"errors": "This good is already on a submitted application"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        good_document = Document.objects.get(id=doc_pk)
        document = get_good_document(good, good_document.id)
        document.delete_s3()

        good_document.delete()
        if GoodDocument.objects.filter(good=good).count() == 0:
            for good_on_application in GoodOnApplication.objects.filter(good=good):
                good_on_application.delete()

        return JsonResponse({"document": "deleted success"})
