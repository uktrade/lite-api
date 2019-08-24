from django.urls import path

from goods import views

app_name = 'goods'

urlpatterns = [
    # ex: /goods/ - View all goods
    path('', views.GoodList.as_view(), name='goods'),
    # ex: /goods/<uuid:pk>/ - View specific good or modify/delete it
    path('<uuid:pk>/', views.GoodDetail.as_view(), name='good'),
    # ex: /goods/<uuid:pk>/documents/ - View all documents on a good or add a new one
    path('<uuid:pk>/documents/', views.GoodDocuments.as_view(), name='documents'),
    # ex: /goods/<uuid:pk>/documents/<uuid:doc_pk>/ - View a specific document (get the download link etc.) or delete it
    path('<uuid:pk>/documents/<uuid:doc_pk>/', views.GoodDocumentDetail.as_view(), name='document'),
    # ex: /goods/flags/
    path('flags/', views.GoodFlagsAssignment.as_view(), name='good_flags'),
    # ex: /goods/<uuid:pk>/activity/
    path('<uuid:pk>/activity/', views.GoodActivity.as_view(), name='activity'),
]
