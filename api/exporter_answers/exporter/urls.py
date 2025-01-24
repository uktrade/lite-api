from django.urls import path

from api.exporter_answers.exporter.views import ExporterAnswerSetViewSet

app_name = "exporter_exporter_answers"

urlpatterns = [
    path(
        "exporter-answer-set/",
        ExporterAnswerSetViewSet.as_view({"get": "list", "post": "create"}),
        name="exporter_answer_set",
    ),
    path(
        "exporter-answer-set/<uuid:exporter_answer_set_id>/",
        ExporterAnswerSetViewSet.as_view({"get": "retrieve", "delete": "delete", "put": "update"}),
        name="exporter_answer_set",
    ),
]
