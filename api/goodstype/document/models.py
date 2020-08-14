from django.db import models

from api.documents.models import Document
from api.goodstype.models import GoodsType


class GoodsTypeDocument(Document):
    goods_type = models.ForeignKey(GoodsType, on_delete=models.CASCADE)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
