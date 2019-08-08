from django.http import JsonResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from cases.enums import CaseType
from cases.models import Case
from clc_queries.models import ClcQuery
from conf.authentication import ExporterAuthentication
from goods.enums import GoodStatus, GoodControlled
from goods.libraries.get_good import get_good
from goods.models import Good
from goods.serializers import GoodSerializer
from organisations.libraries.get_organisation import get_organisation_by_user
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status


class GoodList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        organisation = get_organisation_by_user(request.user)
        description = request.GET.get('description', '')
        part_number = request.GET.get('part_number', '')
        goods = Good.objects.filter(organisation=organisation,
                                    description__icontains=description,
                                    part_number__icontains=part_number).order_by('description')
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
            if not data['validate_only']:
                good = serializer.save()

                if data['is_good_controlled'] == GoodControlled.UNSURE:
                    # automatically raise a CLC query case
                    clc_query = ClcQuery(details=data['not_sure_details_details'],
                                         good=good,
                                         status=get_case_status_from_status(CaseStatusEnum.SUBMITTED))
                    clc_query.save()

                    # Create a case
                    case = Case(clc_query=clc_query, type=CaseType.CLC_QUERY)
                    case.save()

                    # Add said case to default queue
                    queue = Queue.objects.get(pk='00000000-0000-0000-0000-000000000001')
                    queue.cases.add(case)
                    queue.save()

            return JsonResponse(data={'good': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class GoodDetail(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        good = get_good(pk)

        if good.organisation != organisation:
            raise Http404

        serializer = GoodSerializer(good)
        request.user.notification_set.filter(note__case__clc_query__good=good).update(
            viewed_at=timezone.now()
        )
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

        good.delete()
        return JsonResponse(data={'status': 'Good Deleted'},
                            status=status.HTTP_200_OK)
