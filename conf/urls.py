from django.contrib import admin
from django.urls import path, include

from .settings import ADMIN_ENABLED

urlpatterns = [
    path('applications/', include('applications.urls')),
    path('cases/', include('cases.urls')),
    path('drafts/', include('drafts.urls')),
    path('organisations/', include('organisations.urls')),
    path('users/', include('users.urls')),
    path('queues/', include('queues.urls')),
]

if ADMIN_ENABLED:
    urlpatterns += path('admin/', admin.site.urls),

