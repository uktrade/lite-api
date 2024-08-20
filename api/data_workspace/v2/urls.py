from rest_framework.routers import DefaultRouter

from api.data_workspace.v2 import views


router_v2 = DefaultRouter()
router_v2.register(
    "licence-statuses",
    views.LicenceStatusesListView,
    basename="dw-licence-statuses",
)
router_v2.register(
    "licence-decision-types",
    views.LicenceDecisionTypesListView,
    basename="dw-licence-decision-types",
)
