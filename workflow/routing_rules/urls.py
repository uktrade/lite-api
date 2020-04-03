from django.urls import path

from workflow.routing_rules import views

app_name = "routing_rules"

urlpatterns = [
    path("", views.RoutingRulesList.as_view(), name="list"),
    path("<uuid:pk>/", views.RoutingRulesDetail.as_view(), name="detail"),
    path("<uuid:pk>/status/<str:status>/", views.RoutingRulesActiveStatus.as_view(), name="active_status"),
]
