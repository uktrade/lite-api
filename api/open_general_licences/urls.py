from django.urls import path

from api.open_general_licences import views

app_name = "open_general_licences"

urlpatterns = [
    path("", views.OpenGeneralLicenceList.as_view(), name="list"),
    path("<uuid:pk>/", views.OpenGeneralLicenceDetail.as_view(), name="detail"),
    path("<uuid:pk>/activity/", views.OpenGeneralLicenceActivityView.as_view(), name="activity"),
]
