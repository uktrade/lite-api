from django.urls import path

from audit import views

app_name = 'audit'

urlpatterns = [
    path('<str:type>/<uuid:pk>/', views.AuditDetail.as_view(), name='audit_detail'),
]
