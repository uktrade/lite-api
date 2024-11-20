from api.data_workspace.metadata.routers import TableMetadataRouter
from api.data_workspace.v2 import views


router_v2 = TableMetadataRouter()
router_v2.register(views.LicenceDecisionViewSet)
router_v2.register(views.CountryViewSet)
router_v2.register(views.DestinationViewSet)
