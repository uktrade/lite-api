from django.urls import path

from picklist_items import views

app_name = 'picklist_items'

urlpatterns = [
    # /picklist_items/
    # /picklist_items/?type=
    path('', views.PickListItems.as_view(), name='picklist_items'),

    # /picklist_items/<uuid:pk>
    path('<uuid:pk>/', views.PicklistItemDetail.as_view(), name='picklist_item'),
]
