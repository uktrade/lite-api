from django.urls import path

from organisations import views

app_name = 'organisations'

urlpatterns = [
    path('', views.organisations_list, name='organisations'),
    path('<uuid:pk>/', views.organisation_detail, name='organisation'),
    path('validate/', views.Validate.as_view(), name='validate')
]