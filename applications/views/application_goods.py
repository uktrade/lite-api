import reversion
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from applications.libraries.get_goods_on_applications import get_good_on_application
from applications.models import GoodOnApplication
from applications.serializers import GoodOnApplicationViewSerializer, GoodOnApplicationCreateSerializer
from conf.authentication import ExporterAuthentication
from conf.decorators import only_application_type
from goods.enums import GoodStatus
from goods.libraries.get_goods import get_good_with_organisation
from goods.models import GoodDocument
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer


class ApplicationGoodsType(APIView):
    """
    Goods Types belonging to an application
    """
    authentication_classes = (ExporterAuthentication,)

    @only_application_type(ApplicationLicenceType.OPEN_LICENCE)
    def get(self, request, application):
        goods_types = GoodsType.objects.filter(application=application)
        goods_types_data = GoodsTypeSerializer(goods_types, many=True).data

        return JsonResponse(data={'goods': goods_types_data})

    @only_application_type(ApplicationLicenceType.OPEN_LICENCE)
    def delete(self, request, application):
        """
        Deletes a Goods Type
        """
        goods_types = GoodsType.objects.filter(application=application)
        goods_types_data = GoodsTypeSerializer(goods_types, many=True).data

        return JsonResponse(data={'goods': goods_types_data})


class ApplicationGoods(APIView):
    """
    Goods belonging to an application
    """
    authentication_classes = (ExporterAuthentication,)

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    def get(self, request, application):
        goods = GoodOnApplication.objects.filter(application=application)
        goods_data = GoodOnApplicationViewSerializer(goods, many=True).data

        return JsonResponse(data={'goods': goods_data})

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    def post(self, request, application):
        data = request.data
        data['good'] = data['good_id']
        data['application'] = application.id

        good = get_good_with_organisation(data.get('good'), request.user.organisation)

        if len(GoodDocument.objects.filter(good=good)) == 0:
            return JsonResponse(data={'error': 'Cannot attach a good with no documents'},
                                status=status.HTTP_400_BAD_REQUEST)

        with reversion.create_revision():
            serializer = GoodOnApplicationCreateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()

                reversion.set_user(request.user)
                reversion.set_comment("Created Good on Application Revision")

                return JsonResponse(data={'good': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)


class ApplicationGoodsDetails(APIView):
    authentication_classes = (ExporterAuthentication,)

    def delete(self, request, good_on_application_pk):
        good_on_application = get_good_on_application(good_on_application_pk)

        if good_on_application.good.status == GoodStatus.SUBMITTED \
                and GoodOnApplication.objects.filter(good=good_on_application.good).count() == 1:
            good_on_application.good.status = GoodStatus.DRAFT
            good_on_application.good.save()

        good_on_application.delete()

        return JsonResponse({'status': 'success'}, status=status.HTTP_200_OK)
