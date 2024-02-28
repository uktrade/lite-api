import pytest

from faker import Faker

from api.goods.goods_anonymisers import sanitize_serial_number, sanitize_serial_numbers


# NOTE: Force faker to use a seed when producing output so that we can assume a
# deterministic set of results
@pytest.fixture(autouse=True)
def seed_faker():
    Faker.seed(0)


def test_sanitize_serial_number():
    assert sanitize_serial_number("12345") == "serial-number-50494"


def test_sanitize_serial_numbers():
    assert sanitize_serial_numbers('{"12345","6789"}') == '{"serial-number-50494","serial-number-99346"}'
