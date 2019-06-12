from django.urls import path

from queues import views

app_name = 'queues'

urlpatterns = [
    path('', views.QueuesList.as_view(), name='queues'),
    path('<uuid:pk>/', views.QueueDetail.as_view(), name='queue'),
]
