# Copyright (c) 2025, Prilk Consulting BV and Contributors
# See license.txt

from types import SimpleNamespace

import frappe
from erpnext import get_default_company

try:
	from frappe.tests import IntegrationTestCase as TestCase
except ImportError:
	from frappe.tests.utils import FrappeTestCase as TestCase

from edocument.edocument.profiles.peppol.parser import parse_peppol_xml

# Buyer whose VAT number and name match no Company
INVOICE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
	xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
	xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
	<cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
	<cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
	<cbc:ID>INV-1</cbc:ID>
	<cbc:IssueDate>2026-10-01</cbc:IssueDate>
	<cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
	<cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
	<cac:AccountingSupplierParty><cac:Party>
		<cac:PartyLegalEntity><cbc:RegistrationName>Some Supplier</cbc:RegistrationName></cac:PartyLegalEntity>
	</cac:Party></cac:AccountingSupplierParty>
	<cac:AccountingCustomerParty><cac:Party>
		<cbc:EndpointID schemeID="0208">0999999999</cbc:EndpointID>
		<cac:PartyTaxScheme><cbc:CompanyID>BE0999999999</cbc:CompanyID></cac:PartyTaxScheme>
		<cac:PartyLegalEntity><cbc:RegistrationName>Unknown Buyer SNC</cbc:RegistrationName></cac:PartyLegalEntity>
	</cac:Party></cac:AccountingCustomerParty>
	<cac:LegalMonetaryTotal><cbc:PayableAmount currencyID="EUR">0</cbc:PayableAmount></cac:LegalMonetaryTotal>
</Invoice>"""


class TestPEPPOLParserCompany(TestCase):
	def test_uses_edocument_company(self):
		company = frappe.get_all(
			"Company", filters={"name": ["!=", get_default_company()]}, pluck="name", limit=1
		)[0]
		edocument = SimpleNamespace(company=company, matching_data=None)

		pi_data = parse_peppol_xml(INVOICE_XML, None, edocument=edocument)

		self.assertEqual(pi_data["company"], company)

	def test_falls_back_to_default_company(self):
		pi_data = parse_peppol_xml(INVOICE_XML, None)

		self.assertEqual(pi_data["company"], get_default_company())
