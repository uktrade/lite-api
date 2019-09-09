from django.urls import path

from queries.control_list_classifications import views

app_name = 'control_list_classifications'

urlpatterns = [
    # ex: /queries/control-list-classifications/ - List all queries of this type
    path('', views.ControlListClassificationsList.as_view(), name='control_list_classifications'),
    # ex: /queries/control-list-classifications/<int:pk>/ - Retrieve details about a specific query
    path('<int:pk>/', views.ControlListClassificationDetail.as_view(), name='control_list_classification'),
]
