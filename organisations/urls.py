from django.urls import path

from organisations import views

app_name = 'organisations'

urlpatterns = [
    path('', views.organisations_list, name='organisations')
]