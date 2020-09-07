from django.contrib import admin

from api.staticdata import countries


@admin.register(countries.models.Country)
class BaseApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "type",
        "is_eu",
    )
    list_filter = (
        "type",
        "is_eu",
    )
