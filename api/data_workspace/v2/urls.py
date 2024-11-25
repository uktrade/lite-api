from api.data_workspace.metadata.routers import TableMetadataRouter
from api.data_workspace.v2 import views


router_v2 = TableMetadataRouter()
router_v2.register(views.LicenceDecisionViewSet)
router_v2.register(views.CountryViewSet)
router_v2.register(views.DestinationViewSet)
router_v2.register(views.GoodViewSet)
<<<<<<< HEAD
router_v2.register(views.GoodDescriptionViewSet)
=======
router_v2.register(views.GoodOnLicenceViewSet)
>>>>>>> ea66a2a2 (Add goods on licences endpoint initial commit)
router_v2.register(views.ApplicationViewSet)
