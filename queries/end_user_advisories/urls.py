from django.urls import path

from queries.end_user_advisories import views

app_name = 'end_user_advisories'

urlpatterns = [
    # ex: /queries/end_user_advisories/ - View all end user advisories from an organisation
    path('', views.EndUserAdvisoriesList.as_view(), name='end_user_advisories'),
    # ex: /queries/end_user_advisories/<int:pk>/ - View details about a specific end user advisory
    path('<int:pk>/', views.EndUserAdvisoriesDetail.as_view(), name='end_user_advisory')
]
