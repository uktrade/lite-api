from django.urls import path

from . import views  # /PS-IGNORE


app_name = "f680"  # /PS-IGNORE

urlpatterns = [
    path("", views.F680CreateView.as_view(), name="f680"),  # /PS-IGNORE
]
