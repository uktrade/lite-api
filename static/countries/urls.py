from django.urls import path

from static.countries import views

app_name = 'countries'

urlpatterns = [
    path('', views.CountriesList.as_view(), name='countries')
]
