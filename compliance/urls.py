from django.urls import path

from compliance import views

app_name = "compliance"

# urls will be required in future compliance stories, conf has already been set up
urlpatterns = [
    path("<uuid:pk>/status/", views.ComplianceManageStatus.as_view(), name="manage_status",),
]
