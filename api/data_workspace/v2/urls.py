from rest_framework.routers import DefaultRouter

from api.data_workspace.v2 import views


router_v2 = DefaultRouter()

router_v2.register(
    "licence-decisions",
    views.LicenceDecisionViewSet,
    basename="dw-licence-decisions",
)

router_v2.register(
    "applications",
    views.ApplicationViewSet,
    basename="dw-applications",
)

router_v2.register(
    "countries",
    views.CountryViewSet,
    basename="dw-countries",
)

router_v2.register(
    "destinations",
    views.DestinationViewSet,
    basename="dw-destinations",
)

router_v2.register(
    "goods",
    views.GoodViewSet,
    basename="dw-goods",
)

router_v2.register(
    "assessments",
    views.AssessmentViewSet,
    basename="dw-assessments",
)
