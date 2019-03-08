from django.urls import path, include

urlpatterns = [
    path('applications/', include('applications.urls')),
    path('drafts/', include('drafts.urls')),
    path('control_codes/', include('control_codes.urls'))
]
