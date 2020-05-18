from django.urls import path

from gov_users.views import gov_user_views
from gov_users.views import roles_views

app_name = "open_general_licences"

urlpatterns = [
    path("", gov_user_views.GovUserList.as_view(), name="list"),
    path("<uuid:pk>/", gov_user_views.GovUserDetail.as_view(), name="detail"),
    # TODO: status change url
]
