import factory

from open_general_licences import models
from open_general_licences.enums import OpenGeneralLicenceStatus
from static.control_list_entries.helpers import get_control_list_entry


class OpenGeneralLicenceFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    description = factory.Faker("word")
    url = factory.Faker("url")
    case_type = NotImplementedError()
    status = OpenGeneralLicenceStatus.ACTIVE
    registration_required = True

    class Meta:
        model = models.OpenGeneralLicence

    @factory.post_generation
    def control_list_entries(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if not extracted:
            extracted = ["ML1a"]

        for control_list_entry in extracted:
            self.control_list_entries.add(get_control_list_entry(control_list_entry))

    @factory.post_generation
    def countries(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if not extracted:
            extracted = ["CA"]

        for country in extracted:
            self.countries.add(country)
