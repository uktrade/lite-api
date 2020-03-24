import random

from faker.providers import BaseProvider


class OrganisationProvider(BaseProvider):
    # pylint: disable=B311
    def eori_number(self):
        return str(random.randint(0, 99999999999999999))

    # pylint: disable=B311
    def sic_number(self):
        return str(random.randint(1110, 99999))

    # pylint: disable=B311
    def vat_number(self):
        return f"GB{random.randint(1000000, 9999999)}"

    # pylint: disable=B311
    def registration_number(self):
        return str(random.randint(10000000, 99999999))
