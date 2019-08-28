import reversion
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from reversion.models import Version

from cases.libraries.activity_helpers import convert_good_reversion_to_activity
from conf.authentication import ExporterAuthentication, GovAuthentication, SharedAuthentication
from documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from documents.models import Document
from drafts.models import GoodOnDraft
from goods.enums import GoodStatus
from goods.libraries.get_good import get_good, get_good_document
from goods.models import Good, GoodDocument
from goods.serializers import GoodSerializer, GoodDocumentViewSerializer, GoodDocumentCreateSerializer, GoodFlagsAssignmentSerializer, FullGoodSerializer
from organisations.libraries.get_organisation import get_organisation_by_user
from users.models import ExporterUser


class GoodList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        organisation = get_organisation_by_user(request.user)
        description = request.GET.get('description', '')
        part_number = request.GET.get('part_number', '')
        control_rating = request.GET.get('control_rating', '')
        goods = Good.objects.filter(organisation=organisation,
                                    description__icontains=description,
                                    part_number__icontains=part_number,
                                    control_code__icontains=control_rating).order_by('description')
        serializer = GoodSerializer(goods, many=True)
        return JsonResponse(data={'goods': serializer.data},
                            )

    def post(self, request):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        data['organisation'] = organisation.id
        data['status'] = GoodStatus.DRAFT
        serializer = GoodSerializer(data=data)

        if serializer.is_valid():
            serializer.save()

            return JsonResponse(data={'good': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class GoodDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        good = get_good(pk)
        if isinstance(request.user, ExporterUser):
            organisation = get_organisation_by_user(request.user)

            if good.organisation != organisation:
                raise Http404

            serializer = GoodSerializer(good)
            request.user.notification_set.filter(note__case__clc_query__good=good).update(
                viewed_at=timezone.now()
            )
        else:
            serializer = FullGoodSerializer(good)

        return JsonResponse(data={'good': serializer.data})

    def put(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        good = get_good(pk)

        if good.organisation != organisation:
            raise Http404

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(data={'errors': 'This good is already on a submitted application'},
                                status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()

        if data.get('is_good_controlled') == 'unsure':
            for good_on_draft in GoodOnDraft.objects.filter(good=good):
                good_on_draft.delete()

        data['organisation'] = organisation.id
        serializer = GoodSerializer(instance=good, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'good': serializer.data})
        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        good = get_good(pk)

        if good.organisation != organisation:
            raise Http404

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(data={'errors': 'Good is already on a submitted application'},
                                status=status.HTTP_400_BAD_REQUEST)

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
        serializer = GoodDocumentViewSerializer(good_documents, many=True)

        return JsonResponse({'documents': serializer.data})

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

        if good.status == GoodStatus.SUBMITTED:
            delete_documents_on_bad_request(data)
            return JsonResponse(data={'errors': 'This good is already on a submitted application'},
                                status=status.HTTP_400_BAD_REQUEST)

        for document in data:
            document['good'] = good_id
            document['user'] = request.user.id
            document['organisation'] = organisation.id

        serializer = GoodDocumentCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'documents': serializer.data}, status=status.HTTP_201_CREATED)

        delete_documents_on_bad_request(data)
        return JsonResponse({'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


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

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(data={'errors': 'This good is already on a submitted application'},
                                status=status.HTTP_400_BAD_REQUEST)

        good_document = get_good_document(good, doc_pk)
        serializer = GoodDocumentViewSerializer(good_document)
        return JsonResponse({'document': serializer.data})

    @transaction.atomic()
    def delete(self, request, pk, doc_pk):
        """
        Deletes good document
        :param request:
        :param pk:
        :param doc_pk:
        :return:
        """

        good = get_good(pk)
        organisation = get_organisation_by_user(request.user)

        if good.organisation != organisation:
            raise Http404

        if good.status == GoodStatus.SUBMITTED:
            return JsonResponse(data={'errors': 'This good is already on a submitted application'},
                                status=status.HTTP_400_BAD_REQUEST)

        good_document = Document.objects.get(id=doc_pk)
        document = get_good_document(good, good_document.id)
        document.delete_s3()

        good_document.delete()
        if len(GoodDocument.objects.filter(good=good)) == 0:
            for good_on_draft in GoodOnDraft.objects.filter(good=good):
                good_on_draft.delete()

        return JsonResponse({'document': 'deleted success'})


class GoodFlagsAssignment(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Assigns flags to a good
    """

    @transaction.atomic
    def put(self, request):
        data = JSONParser().parse(request)
        response_data = []

        for pk in data['goods']:
            good = get_good(pk)
            serializer = GoodFlagsAssignmentSerializer(data=data, context={'team': request.user.team})

            if serializer.is_valid():
                self._assign_flags(serializer.validated_data.get('flags'), serializer.validated_data.get('note'), good, request.user)
                response_data.append({'good': serializer.data})
            else:
                return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data=response_data, status=status.HTTP_200_OK, safe=False)

    def _assign_flags(self, validated_data, note, good, user):
        previously_assigned_team_flags = good.flags.filter(level='Good', team=user.team)
        previously_assigned_not_team_flags = good.flags.exclude(level='Good', team=user.team)
        add_good_flags = [flag.name for flag in validated_data if flag not in previously_assigned_team_flags]
        remove_good_flags = [flag.name for flag in previously_assigned_team_flags if flag not in validated_data]

        with reversion.create_revision():
            reversion.set_comment(
                ('{"flags": {"removed": ' + str(remove_good_flags) + ', "added": ' + str(add_good_flags) + ', "note": "' + str(note) + '"}}')
                .replace('\'', '"')
            )
            reversion.set_user(user)

            good.flags.set(validated_data + list(previously_assigned_not_team_flags))


class GoodActivity(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Retrieves all activity related to a good
    * Good Updates
    * Good Notes
    * ECJU Queries
    """

    def get(self, request, pk):
        good = get_good(pk)

        version_records = Version.objects.filter(Q(object_id=good.pk))
        activity = []
        for version in version_records:
            activity_item = convert_good_reversion_to_activity(version)
            if activity_item:
                activity.append(activity_item)

        # Sort the activity based on date (newest first)
        activity.sort(key=lambda x: x['date'], reverse=True)

        return JsonResponse(data={'activity': activity})
