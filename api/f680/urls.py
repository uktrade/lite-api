from django.urls import path

from api.f680.views import F680View  # /PS-IGNORE


app_name = "f680"  # /PS-IGNORE

urlpatterns = [
    path("", F680View.as_view(), name="application"),  # /PS-IGNORE
]
