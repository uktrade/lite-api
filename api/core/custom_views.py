from django.http import JsonResponse
from rest_framework.generics import ListAPIView

from api.core.helpers import str_to_bool


class OptionalPaginationView(ListAPIView):
    def paginate_queryset(self, queryset):
        if str_to_bool(self.request.GET.get("disable_pagination")):
            return queryset
        else:
            return super().paginate_queryset(queryset)

    def get_paginated_response(self, data):
        if str_to_bool(self.request.GET.get("disable_pagination")):
            return JsonResponse(data={"results": data})
        else:
            return super().get_paginated_response(data)
