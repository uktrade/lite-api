from datetime import datetime

import factory

from compliance.models import OpenLicenceReturns


class OpenLicenceReturnsFactory(factory.django.DjangoModelFactory):
    file = "\na,b,c,d,e"
    year = datetime.now().year

    class Meta:
        model = OpenLicenceReturns
