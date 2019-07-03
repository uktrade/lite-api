from django.urls import path

from queues import views

app_name = 'queues'

urlpatterns = [
    # ex: /queues/ - View all queues
    path('', views.QueuesList.as_view(), name='queues'),
    # ex: /queues/<uuid:pk>/ - View a specific queue
    path('<uuid:pk>/', views.QueueDetail.as_view(), name='queue'),
    # ex: /queues/<uuid:pk>/case-assignments/ - Assign users to cases, on that particular queue
    path('<uuid:pk>/case-assignments/', views.CaseAssignments.as_view(), name='case_assignment')
]
