from rest_framework.routers import DefaultRouter

from api.data_workspace.v2 import views


router_v2 = DefaultRouter()

router_v2.register(
    "licence-decisions",
    views.LicenceDecisionViewSet,
    basename="dw-licence-decisions",
)

router_v2.register("countries", views.CountryViewSet, basename="dw-countries")
