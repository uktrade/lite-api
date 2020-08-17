from rest_framework import pagination
from rest_framework.response import Response

from api.core.helpers import str_to_bool


class MaxPageNumberPagination(pagination.PageNumberPagination):
    def paginate_queryset(self, queryset, request, view=None):
        if str_to_bool(request.GET.get("disable_pagination", False)):
            return

        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return Response(
            {"count": self.page.paginator.count, "total_pages": self.page.paginator.num_pages, "results": data,}
        )
