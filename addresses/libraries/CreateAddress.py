from addresses.models import Address


class CreateAddress:
    def __init__(self, country, address_line_1, address_line_2, state, zip_code, city):
        new_address = Address(
            country=country,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            state=state,
            zip_code=zip_code,
            city=city)
        new_address.save()
