from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path('', views.UserList.as_view(), name='users'),
    path('authenticate/', views.AuthenticateUser.as_view(), name='authenticate'),
    path('<uuid:pk>/', views.UserDetail.as_view(), name='user'),
]
