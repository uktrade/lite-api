from django.urls import path

from applications import views

app_name = 'applications'

urlpatterns = [
    # ex: /applications/ - List all applications
    path('', views.ApplicationList.as_view(), name='applications'),
    # ex: /applications/<uuid:pk>/ - View an application
    path('<uuid:pk>/', views.ApplicationDetail.as_view(), name='application'),
]
