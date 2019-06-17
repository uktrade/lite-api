from django.urls import path

from gov_users import views

app_name = "gov_users"

urlpatterns = [
    path('', views.GovUserList.as_view(), name='gov_users'),
    path('authenticate/', views.AuthenticateGovUser.as_view(), name='authenticate'),
    path('<uuid:pk>/', views.GovUserDetail.as_view(), name='gov_user'),
]
