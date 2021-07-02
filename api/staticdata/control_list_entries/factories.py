from api.staticdata.control_list_entries import models
import factory


class ControlListEntriesFactory(factory.django.DjangoModelFactory):
    rating = NotImplementedError()
    text = factory.Faker("word")
    parent = None
    category = "test-list"
    controlled = True

    class Meta:
        model = models.ControlListEntry
