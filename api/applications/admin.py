from django.contrib import admin

from api.applications import models


@admin.register(models.BaseApplication)
class BaseApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )


@admin.register(models.PartyOnApplication)
class PartyOnApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "party",
    )


