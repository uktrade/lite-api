from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework import viewsets

from api.core.authentication import ExporterAuthentication
from api.core.permissions import IsExporterInOrganisation
from api.exporter_answers.models import ExporterAnswerSet
from api.exporter_answers.enums import STATUS_ACTIVE

from api.organisations.libraries.get_organisation import get_request_user_organisation


class ExporterAnswerSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExporterAnswerSet
        fields = "__all__"
        read_only_fields = ["id", "answer_fields", "status"]

    target_content_type = serializers.SlugRelatedField(slug_field="model", queryset=ContentType.objects.all())


class ExporterAnswerSetViewSet(viewsets.ModelViewSet):
    authentication_classes = (ExporterAuthentication,)
    permission_classes = [IsExporterInOrganisation]
    serializer_class = ExporterAnswerSetSerializer
    queryset = ExporterAnswerSet.objects.filter(status=STATUS_ACTIVE)
    lookup_url_kwarg = "exporter_answer_set_id"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["target_object_id", "status"]

    def get_queryset(self):
        return self.queryset.filter(created_by=self.request.user.exporteruser)

    def create(self, *args, **kwargs):
        self.request.data["created_by"] = self.request.user.exporteruser
        return super().create(*args, **kwargs)

    def get_organisation(self):
        exporter_answer_set = None
        if self.kwargs.get(self.lookup_url_kwarg):
            try:
                exporter_answer_set = ExporterAnswerSet.objects.get(pk=self.kwargs[lookup_url_kwarg])
            except ExporterAnswerSet.DoesNotExist:
                raise Http404()

        if exporter_answer_set:
            return self.exporter_answer_set.created_by.organisation
        else:
            return get_request_user_organisation(self.request)
