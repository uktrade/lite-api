from django.urls import (
    include,
    path,
)

from ..routers import TableMetadataRouter

from . import views


test_router = TableMetadataRouter()

test_router.register(views.HiddenFieldViewSet)
test_router.register(views.UUIDFieldViewSet)
test_router.register(views.CharFieldViewSet)
test_router.register(views.SerializerMethodFieldViewSet)
test_router.register(views.FloatFieldViewSet)
test_router.register(views.DecimalFieldViewSet)
test_router.register(views.IntegerFieldViewSet)
test_router.register(views.AutoPrimaryKeyViewSet)
test_router.register(views.ExplicitPrimaryKeyViewSet)
test_router.register(views.DateTimeFieldViewSet)
test_router.register(views.ChoiceFieldViewSet)

urlpatterns = [
    path("endpoints/", include(test_router.urls)),
]
