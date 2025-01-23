from django.urls import path, include

urlpatterns = [
    path("applications/", include("api.applications.exporter.urls")),
    path("static/", include("api.staticdata.exporter.urls")),
    path("exporter-answers/", include("api.exporter_answers.exporter.urls")),
]
