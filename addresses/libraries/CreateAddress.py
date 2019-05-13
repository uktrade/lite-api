from addresses.models import Address


class CreateAddress:
    def __init__(self, country, address_line_1, address_line_2, region, postcode, city):
        new_address = Address(
            country=country,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            region=region,
            postcode=postcode,
            city=city)
        new_address.save()
