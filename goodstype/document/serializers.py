from rest_framework import serializers

from documents.libraries.process_document import process_document
from documents.serializers import DocumentViewSerializer
from goodstype.document.models import GoodsTypeDocument
from goodstype.models import GoodsType


class GoodsTypeDocumentViewSerializer(DocumentViewSerializer):
    goods_type = serializers.PrimaryKeyRelatedField(queryset=GoodsType.objects.all())

    class Meta:
        model = GoodsTypeDocument
        fields = (
            "id",
            "name",
            "description",
            "s3_key",
            "size",
            "goods_type",
            "safe",
        )
