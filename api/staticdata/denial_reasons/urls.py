from django.urls import path

from api.staticdata.denial_reasons import views

app_name = "denial-reasons"

urlpatterns = [path("", views.DenialReasonsList.as_view(), name="denial-reasons")]
