from django.urls import path

from flags import views

app_name = "flags"

urlpatterns = [
    # ex: /flags/
    # ex: /flags/?level=&team=
    path("", views.FlagsList.as_view(), name="flags"),
    # ex: /flags/<uuid:pk>
    path("<uuid:pk>/", views.FlagDetail.as_view(), name="flag"),
    # ex: /flags/assign/
    path("assign/", views.AssignFlags.as_view(), name="assign_flags"),
    path("rules/", views.FlaggingRules.as_view(), name="flagging_rules"),
    path("rules/<uuid:pk>/", views.FlaggingRuleDetail.as_view(), name="flagging_rule"),
]
