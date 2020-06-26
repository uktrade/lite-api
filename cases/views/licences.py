from django.db.models import Sum, Max, F
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from cases.enums import AdviceType, AdviceLevel
from conf.authentication import GovAuthentication
from goods.models import Good
from licences.enums import LicenceStatus
from licences.models import Licence, GoodOnLicence
from static.control_list_entries.serializers import ControlListEntrySerializer


class LicencesView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        licence = Licence.objects.filter(application=pk).last()
        if not licence:
            return JsonResponse(data={}, status=status.HTTP_200_OK)

        # Group by good and aggregate usage information
        goods_on_licence = GoodOnLicence.objects.filter(
            licence__application=pk,
            good__good__advice__type__in=[AdviceType.APPROVE, AdviceType.PROVISO],
            good__good__advice__case_id=pk,
            good__good__advice__good_id__isnull=False,
            good__good__advice__level=AdviceLevel.FINAL
        ).distinct().values("good").annotate(
            usage_total=Sum("usage"),
            usage_licenced=Max("quantity"),
            usage_applied_for=F("good__quantity"),
            id=F("good__id"),
            advice_type=F("good__good__advice__type"),
            advice_text=F("good__good__advice__text"),
            advice_proviso=F("good__good__advice__proviso"),
            good_id=F("good__good__id"),
            unit=F("good__unit"),
            value=F("good__value"),
            description=F("good__good__description")
        )
        control_list_entries = {
            good.id: ControlListEntrySerializer(good.control_list_entries.all(), many=True).data
            for good in Good.objects.filter(
                id__in=[good["good_id"] for good in goods_on_licence]
            ).prefetch_related("control_list_entries")
        }

        data = {
            "licence": {
                "id": licence.id,
                "start_date": licence.start_date,
                "status": licence.status,
                "duration": licence.duration,
                "reissued": Licence.objects.filter(application=pk, status=LicenceStatus.REVOKED).exists()
            },
            "goods": [
                {
                    "control_list_entries": control_list_entries[good["good_id"]],
                    "id": good["id"],
                    "unit": good["unit"],
                    "usage_total": good["usage_total"],
                    "usage_licenced": good["usage_licenced"],
                    "usage_applied_for": good["usage_applied_for"],
                    "value": good["value"],
                    "advice": {
                        "type": AdviceType.as_representation(good["advice_type"]),
                        "text": good["advice_text"],
                        "proviso": good["advice_proviso"],
                    }
                }
                for good in goods_on_licence
            ]
        }

        return JsonResponse(data=data, status=status.HTTP_200_OK)
