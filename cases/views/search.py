from django.http import JsonResponse
from rest_framework import generics

from cases.models import Case
from cases.serializers import TinyCaseSerializer
from conf.authentication import GovAuthentication
from conf.pagination import MaxPageNumberPagination
from queues.constants import ALL_CASES_SYSTEM_QUEUE_ID, OPEN_CASES_SYSTEM_QUEUE_ID, MY_TEAMS_QUEUES_CASES_ID
from queues.helpers import get_queue, sort_cases, filter_cases, get_queues
from rest_framework.views import APIView

from queues.models import Queue
from queues.serializers import QueueViewSerializer
from cases import service


class CasesSearchView(generics.GenericAPIView):
    authentication_classes = (GovAuthentication,)
    pagination_class = MaxPageNumberPagination

    def get(self, request):
        cases = service.search_cases(
            queue_id=request.GET.get('queue_id'),
            team=request.user.team if request.GET.get('team') else None,
            status=request.GET.get('status'),
            case_type=request.GET.get('case_type')
        )

        queues = service.get_user_queue_meta(user=request.user)
        statuses = service.get_case_status_list()
        case_types = service.get_case_type_list()

        return JsonResponse(
            {
                'data': {
                    'cases': cases,
                    'filters': {
                        'statuses': statuses,
                        'case_types': case_types,
                        'queues': queues,
                    }
                }
            }
        )
