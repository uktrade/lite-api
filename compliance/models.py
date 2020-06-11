from cases.models import Case, models


class ComplianceSiteCase(Case):
    site = models.ForeignKey(
        "organisations.Site", blank=False, null=False, related_name="compliance", on_delete=models.DO_NOTHING
    )
