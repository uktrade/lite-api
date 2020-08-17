from django.urls import path, include

app_name = "queries"

urlpatterns = [
    path("goods-queries/", include("api.queries.goods_query.urls"),),
    path("end-user-advisories/", include("api.queries.end_user_advisories.urls")),
]
