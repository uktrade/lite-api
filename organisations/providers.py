import random

from faker.providers import BaseProvider


class OrganisationProvider(BaseProvider):
    def eori_number(self):
        # pylint: disable=B311
        return str(random.randint(0, 99999999999999999))

    def sic_number(self):
        # pylint: disable=B311
        return str(random.randint(1110, 99999))

    def vat_number(self):
        # pylint: disable=B311
        return f"GB{random.randint(1000000, 9999999)}"

    def registration_number(self):
        # pylint: disable=B311
        return str(random.randint(10000000, 99999999))
