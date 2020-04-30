import csv

from applications.models import CountryOnApplication
from goodstype.serializers import GoodsTypeSerializer
from static.countries.models import Country


def _set_goods_and_countries_for_open_media_application(application):
    with open("lite_content/lite_api/OEIL_products.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if row["SUBTYPE"] == "MEDIA":
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
                else:
                    print(serializer.errors)

    for country in Country.objects.all():
        CountryOnApplication(country=country, application=application).save()
