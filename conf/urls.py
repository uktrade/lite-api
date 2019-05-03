from django.contrib import admin
from django.urls import path, include

from conf.settings import ADMIN_ENABLED

urlpatterns = [
    path('applications/', include('applications.urls')),
    path('cases/', include('cases.urls')),
    path('drafts/', include('drafts.urls')),
    path('goods/', include('goods.urls')),
    path('organisations/', include('organisations.urls')),
    path('static/units/', include('quantity.urls')),
    path('queues/', include('queues.urls')),
    path('users/', include('users.urls')),
]

if ADMIN_ENABLED:
    urlpatterns += path('admin/', admin.site.urls),

