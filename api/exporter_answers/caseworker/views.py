from django.contrib.contenttypes.models import ContentType
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework import viewsets

from api.core.authentication import GovAuthentication
from api.exporter_answers.models import ExporterAnswerSet


class ExporterAnswerSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExporterAnswerSet
        fields = "__all__"

    target_content_type = serializers.SlugRelatedField(slug_field="model", queryset=ContentType.objects.all())


class ExporterAnswerSetViewSet(viewsets.ModelViewSet):
    authentication_classes = (GovAuthentication,)
    serializer_class = ExporterAnswerSetSerializer
    queryset = ExporterAnswerSet.objects.all()
    lookup_url_kwarg = "exporter_answer_set_id"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["target_object_id", "status"]
