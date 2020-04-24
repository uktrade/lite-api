import factory
from queues.models import Queue
from teams.models import Team


class QueueFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    team = factory.SubFactory("queues.tests.factories.TeamFactory")

    class Meta:
        model = Queue

    @factory.post_generation
    def cases(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing.
            return
        self.cases.set(extracted)


class TeamFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")

    class Meta:
        model = Team
