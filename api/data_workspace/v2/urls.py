from rest_framework.routers import DefaultRouter

from api.data_workspace.v2 import views


router_v2 = DefaultRouter()

router_v2.register(
    "licences",
    views.LicencesListView,
    basename="dw-licences",
)