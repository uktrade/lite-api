from functools import wraps

from django.core.management.base import BaseCommand
from django.core.management import call_command

import requests
import xmltodict


def cache_to_file(filename):
    def wrapper(function):
        @wraps(function)
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
def get_xml():
    response = requests.get('https://scsanctions.un.org/resources/xml/en/consolidated.xml')
    response.raise_for_status()
    return response.content


class Command(BaseCommand):
    def handle(self, *args, **options):
        parsed = xmltodict.parse(
            get_xml(),
            postprocessor=(lambda path, key, value: (key.lower(), value)),
            #force_list=["goods_item", "country", "p"],
            xml_attribs=False,
            cdata_key="p",
        )
        items = set()
        for i, item in enumerate(parsed["consolidated_list"]["individuals"]["individual"]):
            if item['dataid'] in items:
                import pdb; pdb.set_trace()
            items.add(item['dataid'])
            # if item.keys() != parsed["consolidated_list"]["individuals"]["individual"][0].keys():
                # import pdb; pdb.set_trace()

        # parsed["consolidated_list"]["entities"]

        for i, item in enumerate(parsed["consolidated_list"]["entities"]["entity"]):
            if item['dataid'] in items:
                import pdb; pdb.set_trace()
            items.add(item['dataid'])
