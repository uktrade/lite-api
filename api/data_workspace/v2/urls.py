from api.data_workspace.v2 import views

from api.data_workspace.metadata.routers import TableMetadataRouter


router_v2 = TableMetadataRouter()

router_v2.register(
    "licence-decisions",
    views.LicenceDecisionViewSet,
    basename="dw-licence-decisions",
)

router_v2.register("countries", views.CountryViewSet, basename="dw-countries")
