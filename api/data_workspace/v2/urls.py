from api.data_workspace.metadata.routers import TableMetadataRouter
from api.data_workspace.v2 import views

router_v2 = TableMetadataRouter()
router_v2.register(views.LicenceDecisionViewSet)
router_v2.register(views.CountryViewSet)
router_v2.register(views.DestinationViewSet)
router_v2.register(views.GoodViewSet)
router_v2.register(views.GoodDescriptionViewSet)
router_v2.register(views.GoodOnLicenceViewSet)
router_v2.register(views.ApplicationViewSet)
router_v2.register(views.UnitViewSet)
router_v2.register(views.FootnoteViewSet)
router_v2.register(views.AssessmentViewSet)
