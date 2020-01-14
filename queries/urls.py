from django.urls import path, include

app_name = "queries"

urlpatterns = [
    path("control-list-classifications/", include("queries.goods_query.urls"),),
    path("end-user-advisories/", include("queries.end_user_advisories.urls")),
]
