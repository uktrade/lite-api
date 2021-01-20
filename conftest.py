def pytest_configure(settings):
    settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS = "sanctions-alias-test"
    settings.ELASTICSEARCH_DENIALS_INDEX_ALIAS = "denials-alias-test"
