from django.urls import (
    include,
    path,
)

from api.data_workspace.v0.urls import router_v0
from api.data_workspace.v1.urls import router_v1
from api.data_workspace.v2.urls import router_v2


app_name = "data_workspace"

urlpatterns = [
    path("v0/", include((router_v0.urls, "data_workspace_v0"), namespace="v0")),
    path("v1/", include((router_v1.urls, "data_workspace_v1"), namespace="v1")),
    path("v2/", include((router_v2.urls, "data_workspace_v2"), namespace="v2")),
]
