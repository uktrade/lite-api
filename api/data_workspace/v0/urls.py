from rest_framework.routers import DefaultRouter

from api.data_workspace.v0 import licence_views


router_v0 = DefaultRouter()
router_v0.register(
    "licences",
    licence_views.LicencesListDW,
    basename="dw-licences-only",
)
router_v0.register(
    "ogl",
    licence_views.OpenGeneralLicenceListDW,
    basename="dw-ogl-only",
)