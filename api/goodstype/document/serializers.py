from rest_framework import serializers

from api.documents.libraries.process_document import process_document
from api.goodstype.document.models import GoodsTypeDocument
from api.goodstype.models import GoodsType


class GoodsTypeDocumentSerializer(serializers.ModelSerializer):
    goods_type = serializers.PrimaryKeyRelatedField(queryset=GoodsType.objects.all())

    class Meta:
        model = GoodsTypeDocument
        fields = (
            "id",
            "name",
            "s3_key",
            "size",
            "goods_type",
            "safe",
        )

    def create(self, validated_data):
        document = super(GoodsTypeDocumentSerializer, self).create(validated_data)
        document.save()
        process_document(document)
        return document
