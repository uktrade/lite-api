from django.urls import path

from control_codes import views

urlpatterns = [
    path('', views.control_codes_list),
    path('<uuid:id>/', views.control_code_detail)
]
