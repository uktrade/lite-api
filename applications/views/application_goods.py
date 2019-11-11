from django.db import transaction
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from applications.libraries.case_activity import set_application_goods_case_activity, \
    set_application_goods_type_case_activity
from applications.libraries.case_status_helpers import get_case_statuses
from applications.libraries.get_goods_on_applications import get_good_on_application
from applications.models import GoodOnApplication
from applications.serializers import GoodOnApplicationViewSerializer, GoodOnApplicationCreateSerializer
from cases.libraries.activity_types import CaseActivityType
from conf.authentication import ExporterAuthentication
from conf.decorators import application_licence_type, authorised_users, \
    application_in_major_editable_state
from goods.enums import GoodStatus
from goods.libraries.get_goods import get_good_with_organisation
from goods.models import GoodDocument
from goodstype.helpers import get_goods_type
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer
from static.countries.models import Country
from users.models import ExporterUser


class ApplicationGoodsOnApplication(APIView):
    """
    Goods belonging to a standard application
    """
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def get(self, request, application):
        goods = GoodOnApplication.objects.filter(application=application)
        goods_data = GoodOnApplicationViewSerializer(goods, many=True).data

        return JsonResponse(data={'goods': goods_data})

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        data = request.data
        data['good'] = data['good_id']
        data['application'] = application.id

        good = get_good_with_organisation(data.get('good'), request.user.organisation)

        if GoodDocument.objects.filter(good=good).count() == 0:
            return JsonResponse(data={'error': 'Cannot attach a good with no documents'},
                                status=status.HTTP_400_BAD_REQUEST)

        serializer = GoodOnApplicationCreateSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        set_application_goods_case_activity(CaseActivityType.ADD_GOOD_TO_APPLICATION, good.description, request.user,
                                            application)

        return JsonResponse(data={'good': serializer.data}, status=status.HTTP_201_CREATED)


class ApplicationGoodOnApplication(APIView):
    """ Good on a standard application. """
    authentication_classes = (ExporterAuthentication,)

    def delete(self, request, good_on_application_pk):
        good_on_application = get_good_on_application(good_on_application_pk)
        application = good_on_application.application

        if application.status and application.status.status in get_case_statuses(read_only=True):
            return JsonResponse(data={'errors': ['You can only perform this operation when the application '
                                                 'is in an editable state']},
                                status=status.HTTP_400_BAD_REQUEST)

        if good_on_application.application.organisation.id != request.user.organisation.id:
            return JsonResponse(data={'errors': 'Your organisation is not the owner of this good'},
                                status=status.HTTP_403_FORBIDDEN)

        if good_on_application.good.status == GoodStatus.SUBMITTED \
                and GoodOnApplication.objects.filter(good=good_on_application.good).count() == 1:
            good_on_application.good.status = GoodStatus.DRAFT
            good_on_application.good.save()

        good_on_application.delete()

        set_application_goods_case_activity(CaseActivityType.REMOVE_GOOD_FROM_APPLICATION,
                                            good_on_application.good.description, request.user,
                                            good_on_application.application)

        return JsonResponse(data={'status': 'success'}, status=status.HTTP_200_OK)


class ApplicationGoodsTypes(APIView):
    """ Goodstypes belonging to an open application. """
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.OPEN_LICENCE)
    @authorised_users(ExporterUser)
    def get(self, request, application):
        goods_types = GoodsType.objects.filter(application=application)
        goods_types_data = GoodsTypeSerializer(goods_types, many=True).data

        return JsonResponse(data={'goods': goods_types_data}, status=status.HTTP_200_OK)

    @application_licence_type(ApplicationLicenceType.OPEN_LICENCE)
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Post a goodstype
        """
        request.data['application'] = application

        serializer = GoodsTypeSerializer(data=request.data)

        if not serializer.is_valid():
            return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        set_application_goods_type_case_activity(CaseActivityType.ADD_GOOD_TYPE_TO_APPLICATION,
                                                 serializer.data['description'], request.user, application)

        return JsonResponse(data={'good': serializer.data}, status=status.HTTP_201_CREATED)


class ApplicationGoodsType(APIView):
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.OPEN_LICENCE)
    @authorised_users(ExporterUser)
    def get(self, request, application, goodstype_pk):
        """
        Gets a goodstype
        """
        goods_type = get_goods_type(goodstype_pk)
        goods_type_data = GoodsTypeSerializer(goods_type).data

        return JsonResponse(data={'good': goods_type_data}, status=status.HTTP_200_OK)

    @application_licence_type(ApplicationLicenceType.OPEN_LICENCE)
    @authorised_users(ExporterUser)
    def delete(self, request, application, goodstype_pk):
        """
        Deletes a goodstype
        """
        goods_type = get_goods_type(goodstype_pk)
        goods_type.delete()

        set_application_goods_type_case_activity(CaseActivityType.REMOVE_GOOD_TYPE_FROM_APPLICATION,
                                                 goods_type.description, request.user, application)

        return JsonResponse(data={}, status=status.HTTP_200_OK)


class ApplicationGoodsTypeCountries(APIView):
    """
    Sets countries on goodstype
    """
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    @application_licence_type(ApplicationLicenceType.OPEN_LICENCE)
    @authorised_users(ExporterUser)
    def put(self, request, application, goodstype_pk):
        data = request.data

        for good, countries in data.items():
            good = get_goods_type(good)
            if not Country.objects.filter(pk__in=countries).count() == len(countries):
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)

            good.countries.set(countries)

        return JsonResponse(data=data, status=status.HTTP_200_OK)
