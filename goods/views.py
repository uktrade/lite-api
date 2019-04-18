from django.http import JsonResponse, Http404
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from goods.models import Good
from goods.serializers import GoodSerializer
from users.models import User


class GoodList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = User.objects.get(email=request.user)
        organisation = user.organisation

        goods = Good.objects.filter(organisation=organisation).order_by('description')
        serializer = GoodSerializer(goods, many=True)
        return JsonResponse(data={'goods': serializer.data},
                            safe=False)

    def post(self, request):
        user = User.objects.get(email=request.user)
        organisation = user.organisation

        data = JSONParser().parse(request)
        data.organisation = organisation.id
        serializer = GoodSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'good': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class GoodDetail(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        try:
            return Good.objects.get(pk=pk)
        except Good.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        good = self.get_object(pk)
        serializer = GoodSerializer(good)
        return JsonResponse(data={'good': serializer.data})
