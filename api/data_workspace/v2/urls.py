from rest_framework.routers import DefaultRouter

from api.data_workspace.v2.views import application_views


router_v2 = DefaultRouter()
router_v2.register(
    "applications",
    application_views.ApplicationListView,
    basename="dw-applications",
)
router_v2.register(
    "rfis",
    application_views.RFIListView,
    basename="dw-rfis",
)
