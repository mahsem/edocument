# Copyright (c) 2025, Prilk Consulting BV and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from erpnext import get_default_company

try:
	from frappe.tests import IntegrationTestCase as TestCase
except ImportError:
	from frappe.tests.utils import FrappeTestCase as TestCase

IGNORE_TEST_RECORD_DEPENDENCIES = ["Company", "Country", "DocType", "EDocument Profile"]

INVOICE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
	xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
	xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
	<cbc:ID>INV-1</cbc:ID>
	<cac:AccountingSupplierParty><cac:Party>
		<cac:PartyLegalEntity><cbc:RegistrationName>Some Supplier</cbc:RegistrationName></cac:PartyLegalEntity>
	</cac:Party></cac:AccountingSupplierParty>
	<cac:AccountingCustomerParty><cac:Party>
		<cac:PartyLegalEntity><cbc:RegistrationName>{buyer}</cbc:RegistrationName></cac:PartyLegalEntity>
	</cac:Party></cac:AccountingCustomerParty>
</Invoice>"""


class TestEDocumentFieldDetection(TestCase):
	"""The buyer in the XML is one of our companies, as on an invoice between two of them."""

	def _edocument(self, direction):
		edocument = frappe.get_doc(
			{
				"doctype": "EDocument",
				"direction": direction,
				"edocument_profile": frappe.db.get_value(
					"EDocument Profile", {"detector_path": ["like", "%.peppol.detector.%"]}
				),
				"xml_file": "/private/files/invoice.xml",
			}
		)
		xml_bytes = INVOICE_XML.format(buyer=get_default_company()).encode()
		patcher = patch.object(type(edocument), "_get_xml_from_attached_files", return_value=xml_bytes)
		patcher.start()
		self.addCleanup(patcher.stop)
		return edocument

	def test_incoming_detects_company_from_buyer(self):
		detected_fields = self._edocument("Incoming").get_detected_fields()

		self.assertEqual(detected_fields["company"], get_default_company())
		self.assertEqual(detected_fields["edocument_target_type"], "Purchase Invoice")

	def test_outgoing_detects_nothing(self):
		self.assertEqual(self._edocument("Outgoing").get_detected_fields(), {})
