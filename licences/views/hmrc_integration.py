from django.db import transaction
from django.http import HttpResponse, JsonResponse
from rest_framework import serializers, status
from rest_framework.generics import UpdateAPIView

from applications.models import GoodOnApplication
from licences.models import Licence
from licences.serializers.hmrc_integration import HMRCLicenceUsageUpdateSerializer


class HMRCLicenceUsageUpdateView(UpdateAPIView):
    authentication_classes = []
    serializer_class = HMRCLicenceUsageUpdateSerializer

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return JsonResponse(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        licences_status = _validate_licences(serializer.validated_data["licences"])
        if licences_status["valid"]:
            _update_licences_usage(licences_status["valid"])

        return JsonResponse(data={"usage_update_status": licences_status}, status=status.HTTP_201_CREATED)


def _goods_valid_on_licence(licence):
    for g in licence["goods"]:
        if not GoodOnApplication.objects.filter(application__licence__id=licence["id"], good_id=g["id"]).exists():
            return False

    return True


def _validate_licences(licences):
    licence_status = {
        "valid": [],
        "invalid": [],
    }

    for l in licences:
        if not Licence.objects.filter(id=l["id"]).exists() or not _goods_valid_on_licence(l):
            licence_status["invalid"].append(l)
        else:
            licence_status["valid"].append(l)

    return licence_status


def _update_licences_usage(licences):
    with transaction.atomic():
        for l in licences:
            for g in l["goods"]:
                GoodOnApplication.objects.filter(application__licence__id=l["id"], good_id=g["id"]).update(
                    usage=g["usage"]
                )
