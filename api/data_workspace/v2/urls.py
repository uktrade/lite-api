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
    "goods-ratings",
    views.GoodRatingViewSet,
    basename="dw-goods-ratings",
)

router_v2.register(
    "goods-on-licences",
    views.GoodOnLicenceViewSet,
    basename="dw-goods-on-licences",
)

router_v2.register(
    "goods-descriptions",
    views.GoodDescriptionViewSet,
    basename="dw-goods-descriptions",
)

router_v2.register(
    "licences-refusals-criteria",
    views.LicenceRefusalCriteriaViewSet,
    basename="dw-licences-refusals-criteria",
)

router_v2.register(
    "footnotes",
    views.FootnoteViewSet,
    basename="dw-footnotes",
)

router_v2.register(
    "units",
    views.UnitViewSet,
    basename="dw-units",
)
