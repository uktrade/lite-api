from django.urls import path

from quantity import views

app_name = 'quantity'

urlpatterns = [
    path('', views.UnitsList.as_view(), name='quantity')
]
