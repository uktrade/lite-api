from django.urls import path

from queries.goods_query import views

app_name = "goods_queries"

urlpatterns = [
    path("", views.GoodsQueriesCreate.as_view(), name="goods_queries",),
    path("<uuid:pk>/clc-response/", views.GoodQueryCLCResponse.as_view(), name="clc_query_response",),
    path("<uuid:pk>/pv-grading-response/", views.GoodQueryCLCResponse.as_view(), name="pv_grading_query_response",),
    path("<uuid:pk>/status/", views.GoodQueryManageStatus.as_view(), name="manage_status",),
]
