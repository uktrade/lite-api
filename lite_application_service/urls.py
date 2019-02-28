from django.urls import path, include

urlpatterns = [
    path('drafts/', include('drafts.urls')),
    path('applications/', include('applications.urls'))
]
