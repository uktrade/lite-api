from django.urls import path

from api.queues.views import queues, case_assignments

app_name = "queues"

urlpatterns = [
    path("", queues.QueuesList.as_view(), name="queues"),
    path("<uuid:pk>/", queues.QueueDetail.as_view(), name="queue"),
    path("<uuid:pk>/case-assignments/", case_assignments.CaseAssignments.as_view(), name="case_assignments",),
]
