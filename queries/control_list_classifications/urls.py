from django.urls import path

from queries.control_list_classifications import views

app_name = 'control_list_classifications'

urlpatterns = [
    # ex: TODO: Fill in
    path('', views.ControlListClassificationsList.as_view(), name='control_list_classifications'),
    # ex: TODO: Fill in
    path('<uuid:pk>/', views.ControlListClassificationDetail.as_view(), name='control_list_classifications'),
]
