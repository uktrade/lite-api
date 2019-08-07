from django.urls import path

from goods import views

app_name = 'goods'

urlpatterns = [
    path('', views.GoodList.as_view(), name='goods'),
    path('<uuid:pk>/', views.GoodDetail.as_view(), name='good'),
    path('<uuid:pk>/documents', views.GoodDocuments.as_view(), name='documents'),
    path('<uuid:pk>/documents/<str:s3_key>/', views.GoodDocumentDetail.as_view(), name='document'),
    path('<uuid:pk>/documents/<uuid:doc_pk>', views.RemoveGoodDocument.as_view(), name='remove_document')
]
