from django.urls import path

from applications.views import views, application_goods

app_name = 'applications'

urlpatterns = [
    # ex: /applications/ - List all/draft/submitted applications
    # ex: /applications/?submitted=
    path(
        route='',
        view=views.ApplicationList.as_view(),
        name='applications'
    ),
    # ex: /applications/<uuid:pk>/ - View an application
    path(
        route='<uuid:pk>/',
        view=views.ApplicationDetail.as_view(),
        name='application'
    ),
    # ex: /applications/<uuid:pk>/submit/ - Submit an application
    path(
        route='<uuid:pk>/submit/',
        view=views.ApplicationSubmission.as_view(),
        name='application_submit'
    ),
    path(
        route='<uuid:pk>/goods/',
        view=application_goods.ApplicationGoods.as_view(),
        name='application_goods'
    ),
]
