from django.urls import path, include

from api.data_workspace.v0.urls import router_v0
from api.data_workspace.v1.urls import router_v1


app_name = "data_workspace"

urlpatterns = [
    path("v0/", include(router_v0.urls)),
    path("v1/", include(router_v1.urls)),
]
