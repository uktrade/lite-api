from django.urls import path

from queries.goods_query import views

app_name = "goods_queries"

urlpatterns = [
    path("", views.GoodsQueriesList.as_view(), name="goods_queries",),
    path("<uuid:pk>/", views.GoodQueryDetail.as_view(), name="goods_query",),
    path("<uuid:pk>/status/", views.GoodQueryManageStatus.as_view(), name="manage_status",),
]
