from django.contrib import admin

from api.parties import models


@admin.register(models.Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "address",
        "type",
        "sub_type",
    )
    list_filter = (
        "type",
        "sub_type",
    )

