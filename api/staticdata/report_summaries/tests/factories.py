import factory

from ..models import (
    ReportSummaryPrefix,
    ReportSummarySubject,
)


class ReportSummaryPrefixFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReportSummaryPrefix

    name = factory.Faker("word")


class ReportSummarySubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReportSummarySubject

    code_level = 1
    name = factory.Faker("word")
