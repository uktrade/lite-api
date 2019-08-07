from django.urls import path

from ecju_queries import views

app_name = 'ecju_queries'

urlpatterns = [
    # ex: /ecju-queries/
    path('', views.EcjuQueriesList.as_view(), name='ecju_queries'),
    # ex: /ecju-queries/<uuid:pk>
    path('<uuid:pk>/', views.EcjuQueryDetail.as_view(), name='ecju_query'),
]
