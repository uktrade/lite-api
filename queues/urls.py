from django.urls import path

from queues.views import queues, case_assignments

app_name = "queues"

urlpatterns = [
    # ex: /queues/ - View all queues
    path("", queues.QueuesList.as_view(), name="queues"),
    # ex: /queues/<uuid:pk>/ - View a specific queue
    path("<uuid:pk>/", queues.QueueDetail.as_view(), name="queue"),
    # ex: /queues/<uuid:pk>/case-assignments/ - Assign users to a case on that queue
    path(
        "<uuid:pk>/case-assignments/",
        case_assignments.CaseAssignments.as_view(),
        name="case_assignments",
    ),
]
