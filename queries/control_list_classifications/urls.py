from django.urls import path

from queries.control_list_classifications import views

app_name = "control_list_classifications"

urlpatterns = [
    path("", views.ControlListClassificationsList.as_view(), name="control_list_classifications",),
    path("<uuid:pk>/", views.ControlListClassificationDetail.as_view(), name="control_list_classification",),
    path("<uuid:pk>/status/", views.CLCManageStatus.as_view(), name="manage_status",),
    path("<uuid:pk>/generated-documents/", views.GeneratedDocuments.as_view(), name="generated_documents",),
]
