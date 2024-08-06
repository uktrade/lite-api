from rest_framework.routers import DefaultRouter

from api.data_workspace.v2 import views


router_v2 = DefaultRouter()
router_v2.register(
    "applications",
    views.ApplicationListView,
    basename="dw-applications",
)
router_v2.register(
    "rfis",
    views.RFIListView,
    basename="dw-rfis",
)
router_v2.register(
    "statuses",
    views.StatusListView,
    basename="dw-statuses",
)
router_v2.register(
    "status_changes",
    views.StatusChangeListView,
    basename="dw-status-changes",
)
router_v2.register(
    "non_working_days",
    views.NonWorkingDayListView,
    basename="dw-non-working-days",
)
