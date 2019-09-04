from django.urls import path

from goodstype import views

app_name = 'goodstype'

urlpatterns = [
    # ex: /goodstype/
    path('', views.GoodsTypeList.as_view(), name='goodstypes-list'),
    # ex: /goodstype/<uuid:pk>/
    path('<uuid:pk>/', views.GoodsTypeDetail.as_view(), name='goodstypes-detail'),
    # ex: /goodstype/<uuid:pk>/activity/
    path('<uuid:pk>/activity/', views.GoodsTypeActivity.as_view(), name='activity'),
]
