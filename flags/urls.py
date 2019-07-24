from django.urls import path

from flags import views

app_name = 'flags'

urlpatterns = [
    # /flags/
    # /flags/?level=&team=
    path('', views.FlagsList.as_view(), name='flags'),
    # /flags/<uuid:pk>
    path('<uuid:pk>/', views.FlagDetail.as_view(), name='flag'),
]
