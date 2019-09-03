from django.urls import path

from clc_queries import views

app_name = 'clc-queries'

urlpatterns = [
    path('<uuid:pk>/', views.ClcQuery.as_view(), name='clc-query'),
]
