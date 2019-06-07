from django.urls import path

from departments import views

app_name = 'departments'

urlpatterns = [
    path('', views.DepartmentList.as_view(), name='departments'),
    path('<uuid:pk>/', views.DepartmentDetail.as_view(), name='department'),
]
