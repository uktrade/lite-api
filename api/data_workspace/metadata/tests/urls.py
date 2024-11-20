from django.urls import (
    include,
    path,
)

from ..routers import TableMetadataRouter

from . import views


test_router = TableMetadataRouter()

test_router.register(views.FakeTableViewSet)
test_router.register(views.AnotherFakeTableViewSet)
test_router.register(views.DetailOnlyViewSet)

urlpatterns = [
    path("endpoints/", include(test_router.urls)),
]
