from django.urls import path

from api.exporter_answers.caseworker.views import ExporterAnswerSetViewSet

app_name = "caseworker_exporter_answers"

urlpatterns = [
    path(
        "exporter-answer-set/",
        ExporterAnswerSetViewSet.as_view({"get": "list"}),
        name="exporter_answer_set",
    ),
    path(
        "exporter-answer-set/<uuid:exporter_answer_set_id>/",
        ExporterAnswerSetViewSet.as_view({"get": "retrieve"}),
        name="exporter_answer_set",
    ),
]
