from rest_framework.generics import RetrieveAPIView

from api.conf.authentication import GovAuthentication
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeViewSerializer


class RetrieveGoodsType(RetrieveAPIView):
    authentication_classes = (GovAuthentication,)
    queryset = GoodsType.objects.all()
    serializer_class = GoodsTypeViewSerializer
