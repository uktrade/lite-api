from django.urls import path

from api.queues.caseworker.views import bulk_approval

app_name = "caseworker_queues"

urlpatterns = [
    path("<uuid:pk>/bulk-approval/", bulk_approval.BulkApprovalCreateView.as_view(), name="bulk_approval"),
]
