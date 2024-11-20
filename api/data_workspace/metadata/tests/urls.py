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

test_router.register(
    "another-fake-table",
    views.AnotherFakeTableViewSet,
    basename="dw-another-fake-table",
)

test_router.register(
    "detail-only",
    views.DetailOnlyViewSet,
    basename="dw-detail-only-table",
)

urlpatterns = [
    path("endpoints/", include(test_router.urls)),
]
