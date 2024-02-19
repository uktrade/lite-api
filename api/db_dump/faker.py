from faker import Faker

fake = Faker("en-GB")


def sanitize_name(value):
    return fake.name()


def sanitize_first_name(value):
    return fake.first_name()


def sanitize_last_name(value):
    return fake.last_name()


def sanitize_email(value):
    return fake.unique.email()


def sanitize_company_name(value):
    return fake.unique.company()


def sanitize_phone_number(value):
    return "+44" + fake.msisdn()[3:]


def sanitize_address(value):
    return fake.address().replace("\n", ", ")


def sanitize_website(value):
    return fake.domain_name(2)


def sanitize_text(value):
    return fake.paragraph(nb_sentences=5)


def sanitize_street_address(value):
    return fake.street_address()


def sanitize_city(value):
    return fake.city()


def sanitize_postcode(value):
    return fake.postcode()


def sanitize_eori_number(value):
    return "GB" + str(fake.random_number(digits=12))


def sanitize_sic_number(value):
    return str(fake.random_number(digits=5))


def sanitize_vat_number(value):
    return "GB" + str(fake.random_number(digits=9))


def sanitize_registration_number(value):
    return str(fake.random_number(digits=8))
