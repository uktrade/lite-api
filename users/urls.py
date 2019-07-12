from django.urls import path
from rest_framework import routers
from users import views

app_name = "users"

router = routers.SimpleRouter()
router.register(r'notifications', views.NotificationViewset)

urlpatterns = [
    path('', views.UserList.as_view(), name='users'),
    path('authenticate/', views.AuthenticateUser.as_view(), name='authenticate'),
    path('<uuid:pk>/', views.UserDetail.as_view(), name='user'),
] + router.urls
