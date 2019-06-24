from django.urls import path

from flags import views

app_name = 'flags'

urlpatterns = [
    path('', views.FlagsList.as_view(), name='flags'),
    path('<uuid:pk>/', views.FlagDetail.as_view(), name='flag'),
]
