from django.contrib import admin

from cases import models


@admin.register(models.CaseType)
class CaseTypeAdmin(admin.ModelAdmin):
    list_display = (
        "type",
        "sub_type",
        "reference",
    )
    list_filter = (
        "type",
        "sub_type",
    )


@admin.register(models.Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case_type",
        "organisation",
        "submitted_at",
    )
    list_filter = ("case_type", "organisation", "status")


@admin.register(models.CaseReferenceCode)
class CaseReferenceCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "reference_number", "year")
    list_filter = ("year",)


@admin.register(models.CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "is_visible_to_exporter",
    )
    list_filter = ("is_visible_to_exporter",)


@admin.register(models.CaseAssignment)
class CaseAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(models.CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type",
        "visible_to_exporter",
    )
    list_filter = ("visible_to_exporter",)


@admin.register(models.Advice)
class AdviceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type",
        "team",
        "level",
        "good",
        "country",
    )
    list_filter = (
        "type",
        "level",
    )


@admin.register(models.EcjuQuery)
class EcjuQueryAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(models.GoodCountryDecision)
class GoodCountryDecisionAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(models.EnforcementCheckID)
class EnforcementCheckIDAdmin(admin.ModelAdmin):
    list_display = (
        "entity_id",
        "entity_type",
    )
    list_filter = ("entity_type",)


@admin.register(models.CaseReviewDate)
class CaseReviewDateAdmin(admin.ModelAdmin):
    list_display = ("id",)
