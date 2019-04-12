from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path('', views.UserList.as_view(), name='users'),
    path('me/', views.UserMeDetail.as_view(), name='me'),
    path('<uuid:pk>/', views.UserDetail.as_view(), name='user'),
]
