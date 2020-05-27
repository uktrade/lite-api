from django.urls import reverse
from defusedxml import ElementTree

from cases.enforcement_check.import_xml import _extract_and_validate_xml_tree
from test_helpers.clients import DataTestClient


class ImportXML(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("cases:enforcement_check", kwargs={"queue_pk": self.queue.pk})

    def test_import_xml(self):
        xml = """<SPIRE_UPLOAD>
            <SPIRE_RETURNS>
                <CODE1>196</CODE1>
                <CODE2>583</CODE2>
                <FLAG>N</FLAG>
            </SPIRE_RETURNS>
            <SPIRE_RETURNS>
                <CODE1>196</CODE1>
                <CODE2>586</CODE2>
                <FLAG>N</FLAG>
            </SPIRE_RETURNS>
            <SPIRE_RETURNS>
                <CODE1>196</CODE1>
                <CODE2>570</CODE2>
                <FLAG>N</FLAG>
            </SPIRE_RETURNS>
            <SPIRE_RETURNS>
                <CODE1>196</CODE1>
                <CODE2>571</CODE2>
                <FLAG>N</FLAG>
            </SPIRE_RETURNS>
        </SPIRE_UPLOAD>"""
        tree = ElementTree.fromstring(xml)
        _extract_and_validate_xml_tree(tree)
