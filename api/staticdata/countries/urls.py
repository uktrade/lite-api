from django.urls import path

from api.staticdata.countries import views

app_name = "countries"

urlpatterns = [
    path("", views.CountriesList.as_view(), name="countries"),
    path("<str:pk>/", views.CountryDetail.as_view(), name="country"),
]
