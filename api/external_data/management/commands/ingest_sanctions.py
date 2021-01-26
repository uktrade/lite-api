import itertools

from django.conf import settings
from django.core.management.base import BaseCommand

from elasticsearch_dsl import connections
import pyexcel

import requests
import xmltodict

from api.external_data import documents


def get_un_sanctions():
    response = requests.get("https://scsanctions.un.org/resources/xml/en/consolidated.xml")
    response.raise_for_status()
    return xmltodict.parse(
        response.content,
        postprocessor=(lambda path, key, value: (key.lower(), value)),
        xml_attribs=False,
        cdata_key="p",
        force_list=["entity_address", "individual_address"],
    )


def get_office_financial_sanctions_implementation():
    response = requests.get("https://ofsistorage.blob.core.windows.net/publishlive/ConList.xml")
    response.raise_for_status()
    return xmltodict.parse(
        response.content,
        postprocessor=(lambda path, key, value: (key.lower(), value)),
        xml_attribs=False,
        cdata_key="p",
    )


def get_uk_sanctions_list():
    book = pyexcel.get_book(
        url="https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/953470/UK_sanctions_list.ods"
    )
    return parse_ods(book)


def parse_ods(book):
    for sheet_name in book.sheet_names():
        records = iter(book[sheet_name])
        headers = next(records)
        for row in records:
            data = dict(zip(headers, row))
            yield {**data, "sheet": sheet_name}


def join_fields(data, fields):
    return " ".join(data[field] for field in fields if data.get(field))


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--rebuild", default=False, action="store_true")

    def rebuild_index(self):
        connection = connections.get_connection()
        connection.indices.delete(index=settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS, ignore=[404])
        documents.SanctionDocumentType.init()

    def handle(self, *args, **options):
        if options["rebuild"]:
            self.rebuild_index()
        self.populate_united_nations_sanctions()
        self.populate_office_financial_sanctions_implementation()
        self.populate_uk_sanctions_list()

    def populate_united_nations_sanctions(self):
        parsed = get_un_sanctions()

        individuals = parsed["consolidated_list"]["individuals"]["individual"]
        entities = parsed["consolidated_list"]["entities"]["entity"]

        for item in itertools.chain(individuals, entities):
            item.pop("nationality", None)
            address_dicts = item.pop("entity_address", {}) or item.pop("individual_address", {})

            addresses = []
            for address_dict in address_dicts:
                if address_dict:
                    addresses.append(" ".join([item for item in address_dict.values() if item]))

            document = documents.SanctionDocumentType(
                meta={"id": item["dataid"]},
                name=join_fields(item, fields=["first_name", "second_name", "third_name"]),
                address=addresses,
                list_type="UN SC",
                reference=item["dataid"],
                data=item,
            )
            document.save()

    def populate_office_financial_sanctions_implementation(self):
        parsed = get_office_financial_sanctions_implementation()
        for item in parsed["arrayofconsolidatedlist"]["consolidatedlist"]:

            item.pop("nationality", None)
            address = item["fulladdress"]
            postcode = normalize_address(item["postcode"])

            if postcode not in normalize_address(address):
                address += " " + postcode

            document = documents.SanctionDocumentType(
                meta={"id": f'OFSI:{item["id"]}'},
                name=item["fullname"],
                address=address,
                postcode=postcode,
                list_type="OFSI",
                reference=item["id"],
                data=item,
            )
            document.save()

    def populate_uk_sanctions_list(self):
        parsed = get_uk_sanctions_list()
        for item in parsed:

            item.pop("nationality", None)
            address = join_fields(item, fields=["Address Line 1", "Address Line 2", "Address Line 3", "Address Line 4"])
            postcode = normalize_address(item["Postcode"])
            if postcode not in normalize_address(address):
                address += " " + postcode

            document = documents.SanctionDocumentType(
                # no unique id for this
                name=item["Primary Name"],
                address=address,
                postcode=postcode,
                list_type="UK sanction",
                reference=item["Unique ID"],
                data=item,
            )
            document.save()


def normalize_address(value):
    if value.lower() in ["unknown", None, ""]:
        return None
    return value.replace(" ", "")
