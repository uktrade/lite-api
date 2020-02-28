from django.db import models

from documents.models import Document
from goodstype.models import GoodsType


class GoodsTypeDocument(Document):
    goods_type = models.ForeignKey(GoodsType, on_delete=models.CASCADE)
