from django.urls import path

from organisations import views

app_name = 'organisations'

urlpatterns = [
    path('', views.OrganisationsList.as_view(), name='organisations'),
    path('<uuid:pk>/', views.OrganisationsDetail.as_view(), name='organisation'),
]
