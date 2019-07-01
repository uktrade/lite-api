from django.urls import path

from addresses import views

app_name = "addresses"

urlpatterns = [
    path('', views.Address.as_view(), name='gov_users'),
]
