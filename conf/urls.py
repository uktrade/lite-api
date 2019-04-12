from django.contrib import admin
from django.urls import path, include

from .settings import ADMIN_ENABLED

urlpatterns = [
    path('applications/', include('applications.urls')),
    path('cases/', include('cases.urls')),
    path('drafts/', include('drafts.urls')),
    path('organisations/', include('organisations.urls')),
    path('queues/', include('queues.urls')),
    path('users/', include('users.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]

if ADMIN_ENABLED:
    urlpatterns += path('admin/', admin.site.urls),

