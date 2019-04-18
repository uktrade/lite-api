from django.contrib import admin
from django.urls import path, include

from conf.settings import ADMIN_ENABLED

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('applications/', include('applications.urls')),
    path('cases/', include('cases.urls')),
    path('drafts/', include('drafts.urls')),
    path('goods/', include('goods.urls')),
    path('organisations/', include('organisations.urls')),
    path('queues/', include('queues.urls')),
    path('users/', include('users.urls')),
    path('users/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if ADMIN_ENABLED:
    urlpatterns += path('admin/', admin.site.urls),

