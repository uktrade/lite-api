from django.urls import path

from api.amendments import views

app_name = "amendments"

urlpatterns = [
    path("create-application-copy/<uuid:case_pk>/", views.CreateApplicationCopyView.as_view(), name="create_application_copy"),
]
