from django.urls import path, include

urlpatterns = [
    path('applications/', include('applications.urls')),
    path('drafts/', include('drafts.urls')),
    path('organisations/', include('organisations.urls')),
    path('users/', include('users.urls')),
]
