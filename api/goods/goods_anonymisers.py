import re

from faker import Faker

fake = Faker("en-GB")


def sanitize_serial_number(value):
    return "serial-number-" + str(fake.random_number(digits=5))


def sanitize_serial_numbers(value):
    serial_numbers = re.findall(r'"(.*?)"', value)
    sanitized_serial_numbers = [f'"{sanitize_serial_number(item)}"' for item in serial_numbers]
    return f"{{{','.join(sanitized_serial_numbers)}}}"
