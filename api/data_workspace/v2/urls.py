from api.data_workspace.v2 import views

from api.data_workspace.metadata.routers import TableMetadataRouter


router_v2 = TableMetadataRouter()
router_v2.register(views.LicenceDecisionViewSet)
router_v2.register(views.CountryViewSet)
