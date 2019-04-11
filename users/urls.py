from django.urls import path

from users import views

app_name = 'users'

urlpatterns = [
    # path('', views.userss_list, name='users'),
    # path('<uuid:pk>/', views.user_detail, name='user')
    path('login/', views.UserLogin.as_view(), name='login')
]