import factory
from api.queues.models import Queue


class QueueFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    team = factory.SubFactory("teams.tests.factories.TeamFactory")
    countersigning_queue = None

    class Meta:
        model = Queue

    @factory.post_generation
    def cases(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing.
            return
        self.api.cases.set(extracted)
