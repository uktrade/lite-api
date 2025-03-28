from django.urls import path, include

urlpatterns = [
    path("queues/", include("api.queues.caseworker.urls")),
    path("applications/", include("api.applications.caseworker.urls")),
    path("organisations/", include("api.organisations.caseworker.urls")),
    path("static/", include("api.staticdata.caseworker.urls")),
    path("gov_users/", include("api.gov_users.caseworker.urls")),
    path("letter_templates/", include("api.letter_templates.caseworker.urls")),
    path("f680/", include("api.f680.caseworker.urls")),
]
