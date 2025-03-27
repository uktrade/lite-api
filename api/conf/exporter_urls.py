from django.urls import path, include

urlpatterns = [
    path("applications/", include("api.applications.exporter.urls")),
    path("export-licences/", include("api.export_licences.exporter.urls")),
    path("static/", include("api.staticdata.exporter.urls")),
    path("f680/", include("api.f680.exporter.urls")),
]
