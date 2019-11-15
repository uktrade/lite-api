from django.http import Http404

from goodstype.document.models import GoodsTypeDocument
from goodstype.models import GoodsType


def get_goods_type(pk):
    try:
        return GoodsType.objects.get(pk=pk)
    except GoodsType.DoesNotExist:
        raise Http404


def delete_goods_type_document_if_exists(goods_type: GoodsType):
    try:
        document = GoodsTypeDocument.objects.get(goods_type=goods_type)
        document.delete_s3()
        document.delete()
    except GoodsTypeDocument.DoesNotExist:
        pass
