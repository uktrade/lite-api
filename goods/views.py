from django.http import JsonResponse, Http404
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from goods.models import Good
from goods.serializers import GoodSerializer
from organisations.libraries.get_organisation import get_organisation_by_user


class GoodList(APIView):
    authentication_classes = (PkAuthentication,)

    def get(self, request):
        organisation = get_organisation_by_user(request.user)
        description = request.GET.get('description', '')
        part_number = request.GET.get('part_number', '')
        goods = Good.objects.filter(organisation=organisation,
                                    description__icontains=description,
                                    part_number__icontains=part_number).order_by('description')
        serializer = GoodSerializer(goods, many=True)
        return JsonResponse(data={'goods': serializer.data},
                            safe=False)

    def post(self, request):
        organisation = get_organisation_by_user(request.user)

        data = JSONParser().parse(request)
        data['organisation'] = organisation.id
        serializer = GoodSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'good': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class GoodDetail(APIView):
    authentication_classes = (PkAuthentication,)

    def get_object(self, pk):
        try:
            return Good.objects.get(pk=pk)
        except Good.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        good = self.get_object(pk)

        if good.organisation != organisation:
            raise Http404

        serializer = GoodSerializer(good)
        return JsonResponse(data={'good': serializer.data})
