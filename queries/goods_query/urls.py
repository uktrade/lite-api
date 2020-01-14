from django.urls import path

from queries.goods_query import views

app_name = "control_list_classifications"

urlpatterns = [
    path("", views.ControlListClassificationsList.as_view(), name="control_list_classifications",),
    path("<uuid:pk>/", views.ControlListClassificationDetail.as_view(), name="control_list_classification",),
    path("<uuid:pk>/status/", views.CLCManageStatus.as_view(), name="manage_status",),
]
