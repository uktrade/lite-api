from django.urls import path, include

app_name = 'static'

urlpatterns = [
    path('control-list-entries/', include('static.control_list_entries.urls')),
    path('countries/', include('static.countries.urls')),
    path('denial-reasons/', include('static.denial_reasons.urls')),
    path('letter-layouts/', include('static.letter_layouts.urls')),
    path('units/', include('static.units.urls')),
    path('statuses/', include('static.statuses.urls')),
]
