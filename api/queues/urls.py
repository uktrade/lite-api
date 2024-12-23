from django.urls import path

from api.queues.views import bulk_approval, queues, case_assignments

app_name = "queues"

urlpatterns = [
    path("", queues.QueuesList.as_view(), name="queues"),
    path("<uuid:pk>/", queues.QueueDetail.as_view(), name="queue"),
    path(
        "<uuid:pk>/case-assignments/",
        case_assignments.CaseAssignments.as_view(),
        name="case_assignments",
    ),
    path("<uuid:pk>/bulk-approval/", bulk_approval.BulkApprovalCreateView.as_view(), name="bulk_approval"),
]
