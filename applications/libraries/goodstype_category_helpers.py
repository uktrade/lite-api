import csv

from applications.models import CountryOnApplication
from goodstype.serializers import GoodsTypeSerializer
from static.countries.models import Country


def set_destinations_for_uk_continental_shelf_application(application):
    country = Country.include_special_countries.get(id="UKCS")
    CountryOnApplication(country=country, application=application).save()


def set_goods_and_countries_for_open_dealer_application(application):
    _add_goodstypes_from_csv("DEALER", application)
    CountryOnApplication.objects.bulk_create(
        [
            CountryOnApplication(country=country, application=application)
            for country in Country.objects.filter(is_eu=True).exclude(id="GB")
        ]
    )


def set_goods_and_countries_for_open_media_application(application):
    _add_goodstypes_from_csv("MEDIA", application)

    CountryOnApplication.objects.bulk_create(
        [CountryOnApplication(country=country, application=application) for country in Country.objects.exclude(id="GB")]
    )


def set_goods_and_countries_for_open_crypto_application(application):
    _add_goodstypes_from_csv("CRYPTO", application)
    with open("lite_content/lite_api/permitted_countries_cryptographic.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        CountryOnApplication.objects.bulk_create(
            [CountryOnApplication(country_id=row["id"], application=application) for row in reader]
        )


def _add_goodstypes_from_csv(category: str, application):
    with open("lite_content/lite_api/OEIL_products.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if row["SUBTYPE"] == category:
                data = {
                    "application": application,
                    "description": row["DESCRIPTION"],
                    "is_good_controlled": "True",
                    "is_good_incorporated": "False",
                    "control_list_entries": row["CONTROL_ENTRY"].split(", "),
                    "report_summary": row["ARS"],
                }
                serializer = GoodsTypeSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
