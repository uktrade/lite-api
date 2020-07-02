from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from licences.models import Licence
from licences.service import get_goods_on_licence


class LicencesView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        # Prioritise getting draft licences, followed by active licences
        # Does not allow fetching of cancelled/surrendered licences
        try:
            licence = Licence.objects.get_draft_licence()
        except Licence.DoesNotExist:
            try:
                licence = Licence.objects.get_active_licence()
            except Licence.DoesNotExist:
                raise NotFound({"non_field_errors": ["No licence found"]})

        # Group by good and aggregate usage information
        goods = get_goods_on_licence(licence, include_control_list_entries=True)

        data = {
            "licence": {
                "id": licence.id,
                "start_date": licence.start_date,
                "status": licence.status,
                "duration": licence.duration,
            },
            "goods": goods,
        }

        return JsonResponse(data=data, status=status.HTTP_200_OK)
