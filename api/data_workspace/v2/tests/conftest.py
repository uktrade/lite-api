import pytest


def pytest_bdd_apply_tag(tag, function):
    if tag == "db":
        marker = pytest.mark.django_db()
        marker(function)
        return True

    return None
