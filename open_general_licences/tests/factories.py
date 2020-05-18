import factory

from open_general_licences import models


class OpenGeneralLicenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.OpenGeneralLicence
