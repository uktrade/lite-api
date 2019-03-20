from django.urls import path

from organisations import views

urlpatterns = [
    path('', views.organisations_list)
]