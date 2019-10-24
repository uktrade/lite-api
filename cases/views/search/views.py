from django.core.exceptions import ValidationError
from django.http import JsonResponse, Http404
from rest_framework import generics

from cases.serializers import TinyCaseSerializer
from cases.views.search import service
from conf.authentication import GovAuthentication
from conf.pagination import MaxPageNumberPagination


class CasesSearchView(generics.GenericAPIView):
    authentication_classes = (GovAuthentication,)
    pagination_class = MaxPageNumberPagination

    def get(self, request):
        case_qs = service.search_cases(
            queue_id=request.GET.get('queue_id'),
            team=request.user.team if request.GET.get('team') else None,
            status=request.GET.get('status'),
            case_type=request.GET.get('case_type'),
            sort=request.GET.get('sort', '')
        )

        try:
            cases = TinyCaseSerializer(case_qs, many=True).data
        except ValidationError:
            cases = []

        queues = service.get_user_queue_meta(user=request.user)
        statuses = service.get_case_status_list()
        case_types = service.get_case_type_list()

        return JsonResponse(
            {
                'data': {
                    'queues': queues,
                    'cases': cases,
                    'filters': {
                        'statuses': statuses,
                        'case_types': case_types,
                    }
                }
            }
        )
