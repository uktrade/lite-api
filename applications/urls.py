from django.urls import path

from applications import views

app_name = 'applications'

urlpatterns = [
    path('', views.ApplicationList.as_view(), name='applications'),
    path('<uuid:pk>/', views.ApplicationDetail.as_view(), name='application'),
    path('clcs/', views.CLCList.as_view(), name='clcs')
]
