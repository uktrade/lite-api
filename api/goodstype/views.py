from rest_framework.generics import RetrieveAPIView

from api.core.authentication import GovAuthentication
from api.goodstype.models import GoodsType
from api.goodstype.serializers import GoodsTypeViewSerializer


class RetrieveGoodsType(RetrieveAPIView):
    authentication_classes = (GovAuthentication,)
    queryset = GoodsType.objects.all()
    serializer_class = GoodsTypeViewSerializer
