import reversion
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from applications.libraries.get_applications import get_draft_with_organisation, get_draft
from applications.models import GoodOnApplication
from applications.serializers import GoodOnApplicationViewSerializer, GoodOnApplicationCreateSerializer
from conf.authentication import ExporterAuthentication
from goods.libraries.get_goods import get_good_with_organisation
from goods.models import GoodDocument
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer
from organisations.libraries.get_organisation import get_organisation_by_user


class DraftGoodsType(APIView):
    """
    View goods belonging to a draft, or add one
    """
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Gets draft Goods Types
        """
        draft = get_draft(pk)
        goods_types_data = list()

        if draft.licence_type == ApplicationLicenceType.OPEN_LICENCE:
            goods_types = GoodsType.objects.filter(application=draft)
            goods_types_data = GoodsTypeSerializer(goods_types, many=True).data

        return JsonResponse(data={'goods': goods_types_data})


class DraftGoods(APIView):
    authentication_classes = (ExporterAuthentication,)
    """
    View goods belonging to a draft, or add one
    """
    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        draft = get_draft_with_organisation(pk, organisation)

        goods_data = list()

        if draft.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
            goods = GoodOnApplication.objects.filter(application=draft)
            goods_data = GoodOnApplicationViewSerializer(goods, many=True).data

        return JsonResponse(data={'goods': goods_data})

    def post(self, request, pk):
        data = JSONParser().parse(request)
        data['good'] = data['good_id']
        data['application'] = str(pk)

        organisation = get_organisation_by_user(request.user)
        get_draft_with_organisation(pk, organisation)
        good = get_good_with_organisation(data.get('good'), organisation)

        if len(GoodDocument.objects.filter(good=good)) == 0:
            return JsonResponse(data={'error': 'Cannot attach a good with no documents'},
                                status=status.HTTP_400_BAD_REQUEST)

        with reversion.create_revision():
            serializer = GoodOnApplicationCreateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()

                reversion.set_user(request.user)
                reversion.set_comment("Created Good on Draft Revision")

                return JsonResponse(data={'good': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
