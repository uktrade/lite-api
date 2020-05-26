import random

from faker.providers import BaseProvider


class OrganisationProvider(BaseProvider):
    def eori_number(self):
        return str(random.randint(0, 99999999999999999))  # nosec

    def sic_number(self):
        return str(random.randint(1110, 99999))  # nosec

    def vat_number(self):
        return f"GB{random.randint(100000000, 999999999)}"  # nosec

    def registration_number(self):
        return str(random.randint(10000000, 99999999))  # nosec
