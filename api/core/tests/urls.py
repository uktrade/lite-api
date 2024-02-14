from django.urls import path

from .views import (
    MisconfiguredParentFilterView,
    ParentFilterView,
)

urlpatterns = [
    path(
        "misconfigured-parent/<str:pk>/child/<str:child_pk>/",
        MisconfiguredParentFilterView.as_view(),
        name="test-misconfigured-parent-filter",
    ),
    path(
        "parent/<str:pk>/child/<str:child_pk>/",
        ParentFilterView.as_view(),
        name="test-parent-filter",
    ),
]
