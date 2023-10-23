import pytest
from django_test_migrations.migrator import Migrator
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestCountryTradingCode(MigratorTestCase):

    migrate_from = ("countries", "0005_country_trading_country_code")
    migrate_to = ("countries", "0006_update_trading_country_code")

    def test_migration_0006_update_trading_country_code(self):
        Country = self.new_state.apps.get_model("countries", "Country")

        mapping = (
            ("AX", "FI"),
            ("BAT", "AQ"),
            ("ES-CE", "XC"),
            ("ES-ML", "XL"),
            ("MC", "FR"),
            ("PR", "US"),
            ("RS", "XS"),
        )
        for country_code, trading_country_code in mapping:
            country = Country.objects.get(id=country_code)
            self.assertEqual(
                country.trading_country_code,
                trading_country_code,
            )

        # Make sure that no other countries have had their country code set
        self.assertEqual(
            Country.objects.exclude(
                id__in=[country_code for country_code, _ in mapping],
            )
            .filter(trading_country_code__isnull=False)
            .count(),
            0,
        )
