from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt import views as jwt_views

from conf.settings import ADMIN_ENABLED

urlpatterns = [
    path('applications/', include('applications.urls')),
    path('cases/', include('cases.urls')),
    path('drafts/', include('drafts.urls')),
    path('organisations/', include('organisations.urls')),
    path('queues/', include('queues.urls')),
    path('users/', include('users.urls')),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
]

if ADMIN_ENABLED:
    urlpatterns += path('admin/', admin.site.urls),

