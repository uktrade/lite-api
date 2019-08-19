from django.urls import path
from rest_framework import routers

from users import views

app_name = "users"

router = routers.SimpleRouter()
router.register(r'notifications', views.NotificationViewset,)
router.register(r'clc_notifications', views.ClcNotificationViewset,)

urlpatterns = [
    # ex: /users/
    path('', views.UserList.as_view(), name='users'),
    # ex: /users/authenticate/
    path('authenticate/', views.AuthenticateExporterUser.as_view(), name='authenticate'),
    # ex: /users/<uuid:pk>/
    path('<uuid:pk>/', views.UserDetail.as_view(), name='user'),
    # ex: /users/me/
    path('me/', views.UserMeDetail.as_view(), name='me'),
    path('authenticate/tokens/', views.ExporterTokens.as_view(), name='tokens')
] + router.urls
