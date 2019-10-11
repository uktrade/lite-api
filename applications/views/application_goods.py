import reversion
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from applications.libraries.get_applications import get_application
from applications.libraries.get_goods_on_applications import get_good_on_application
from applications.models import GoodOnApplication
from applications.serializers import GoodOnApplicationViewSerializer, GoodOnApplicationCreateSerializer
from conf.authentication import ExporterAuthentication
from conf.decorators import only_application_type
from goods.libraries.get_goods import get_good_with_organisation
from goods.models import GoodDocument
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer


class ApplicationGoodsType(APIView):
    """
    View goods belonging to a draft, or add one
    """
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Gets draft Goods Types
        """
        draft = get_application(pk)
        goods_types_data = []

        if draft.licence_type == ApplicationLicenceType.OPEN_LICENCE:
            goods_types = GoodsType.objects.filter(application=draft)
            goods_types_data = GoodsTypeSerializer(goods_types, many=True).data

        return JsonResponse(data={'goods': goods_types_data})


class ApplicationGoods(APIView):
    authentication_classes = (ExporterAuthentication,)
    """
    View goods belonging to a draft, or add one
    """

    def get(self, request, pk):
        draft = get_application(pk=pk, organisation_id=request.user.organisation.id)

        goods_data = []

        if draft.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
            goods = GoodOnApplication.objects.filter(application=draft)
            goods_data = GoodOnApplicationViewSerializer(goods, many=True).data

        return JsonResponse(data={'goods': goods_data})

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    def post(self, request, draft):
        data = request.data
        data['good'] = data['good_id']
        data['application'] = draft.id

        good = get_good_with_organisation(data.get('good'), request.user.organisation)

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


class ApplicationGoodsDetails(APIView):
    def delete(self, request, good_on_application_pk):
        good_on_application = get_good_on_application(good_on_application_pk)

        good_on_application.delete()

        return JsonResponse({'status': 'success'}, status=status.HTTP_200_OK)
