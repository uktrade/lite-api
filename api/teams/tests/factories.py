import factory
from api.teams.models import Team, Department


class DepartmentFactory(factory.django.DjangoModelFactory):
    name = factory.Iterator(["HMRC", "MOD", "BEIS", "DIT", "NCSC"])
    # Commented out since probably we want to manually add this.
    # team = factory.RelatedFactory(
    #     TeamFactory,
    #     factory_related_name='department',
    # )

    class Meta:
        model = Department


class TeamFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    department = factory.SubFactory(DepartmentFactory)

    class Meta:
        model = Team
