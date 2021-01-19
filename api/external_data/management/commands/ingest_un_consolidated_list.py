import io
import functools
import json
import itertools

from django.core.management.base import BaseCommand
from django.core.management import call_command

from elasticsearch import Elasticsearch
from elasticsearch_dsl import connections
import pyexcel

import requests
import xmltodict

from api.external_data import documents


def cache_to_file(filename):
    def wrapper(function):
        @functools.wraps(function)
        def inner(*args):
            try:
                with open(filename, 'rb') as f:
                    return f.read()
            except FileNotFoundError:
                xml = function(*args)
                with open(filename, 'wb') as f:
                    f.write(xml)
                return xml
        return inner
    return wrapper


@cache_to_file('consolidated_un_list.xml')
def get_un_sanctions_xml():
    response = requests.get('https://scsanctions.un.org/resources/xml/en/consolidated.xml')
    response.raise_for_status()
    return response.content


@cache_to_file('office_financial_sanctions_implementation.xml')
def get_office_financial_sanctions_implementation_xml():
    response = requests.get('https://ofsistorage.blob.core.windows.net/publishlive/ConList.xml')
    response.raise_for_status()
    return response.content


def get_uk_sanctions_list_ods():
    return pyexcel.get_book(url='https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/953470/UK_sanctions_list.ods')


def parse_xml(xml):
    return xmltodict.parse(
        xml,
        postprocessor=(lambda path, key, value: (key.lower(), value)),
        xml_attribs=False,
        cdata_key="p",
    )


def parse_ods(book):
    for sheet_name in book.sheet_names():
        records = iter(book[sheet_name])
        headers = next(records)
        for row in records:
            data = dict(zip(headers, row))
            data['sheet'] = sheet_name
            yield data


def build_name(data, fields):
    return ' '.join(data[field] for field in fields if data.get(field))


class Command(BaseCommand):

    def rebuild_index(self):
        connection = connections.get_connection()
        connection.indices.delete(index=documents.SanctionDocumentType.Index.name)
        documents.SanctionDocumentType.init()

    def handle(self, *args, **options):
        self.rebuild_index()
        self.populate_united_nations_sanctions()
        self.populate_office_financial_sanctions_implementation()
        self.populate_uk_sanctions_list()

    def populate_united_nations_sanctions(self):
        parsed = parse_xml(get_un_sanctions_xml())
        
        individuals = parsed["consolidated_list"]["individuals"]["individual"]
        entities = parsed["consolidated_list"]["entities"]["entity"]

        for item in itertools.chain(individuals, entities):
            name = build_name(item, fields=['first_name', "second_name", "third_name"])

            item.pop('nationality', None)

            document = documents.SanctionDocumentType(
                meta={'id': item['dataid']},
                name=name,
                list_type='UN SC',
                reference=item['dataid'],
                data=item,
            )
            document.save()

    def populate_office_financial_sanctions_implementation(self):
        parsed = parse_xml(get_office_financial_sanctions_implementation_xml())

        for item in parsed['arrayofconsolidatedlist']['consolidatedlist']:
            name = build_name(item, fields=['name1', 'name2', 'name3', 'name4', 'name5', 'name6'])

            item.pop('nationality', None)

            document = documents.SanctionDocumentType(
                meta={'id': item['fcoid']},
                name=name,
                list_type='OFSI',
                reference=f'OFSI:{item["id"]}',
                data=item,
            )
            document.save()

    def populate_uk_sanctions_list(self):
        book = get_uk_sanctions_list_ods()
        parsed = parse_ods(book)
        for item in parsed:

            item.pop('nationality', None)

            document = documents.SanctionDocumentType(
                # no unique id for this
                name=item['Primary Name'],
                list_type='UK sanction',
                reference=f'{item["Unique ID"]}',
                data=item,
            )
            document.save()
