from django.urls import path

from documents import views

app_name = "documents"

urlpatterns = [
    path("<uuid:pk>/", views.DocumentDetail.as_view(), name="document"),
]
