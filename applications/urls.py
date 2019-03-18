from django.urls import path

from applications import views

app_name = 'applications'
urlpatterns = [
    path('', views.ApplicationList.as_view()),
    path('test', views.TestData.as_view()),
    path('<uuid:pk>/', views.ApplicationDetail.as_view()),
]
