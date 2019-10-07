from rest_framework import serializers

from documents.models import Document


class DocumentViewSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    s3_key = serializers.SerializerMethodField()

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else 'File not ready'

    class Meta:
        model = Document
        fields = ('name', 's3_key', 'size', 'created_at', 'safe')
