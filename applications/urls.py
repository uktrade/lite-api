from django.urls import path

from applications import views

urlpatterns = [
    path('', views.applications_list),
    path('test/', views.test_data),
    path('<uuid:id>/', views.application_detail),
]
