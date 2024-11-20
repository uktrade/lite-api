from django.urls import (
    include,
    path,
)

from ..routers import TableMetadataRouter

from . import views


test_router = TableMetadataRouter()

test_router.register(
    "fake-table",
    views.FakeTableViewSet,
    basename="dw-fake-table",
)


urlpatterns = [
    path("endpoints/", include(test_router.urls)),
]
