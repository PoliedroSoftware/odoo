from decimal import Decimal
from unittest import SkipTest

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestColombianInvoiceRounding(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].search([
            ('name', '=', 'Holding La Labranza SAS'),
            ('currency_id.name', '=', 'COP'),
            ('account_fiscal_country_id.code', '=', 'CO'),
        ], limit=1) or cls.env.company
        cls.company = cls.company.with_company(cls.company)
        cls.accounts = cls.env['account.account'].with_company(cls.company)
        cls.income_account = cls.accounts.search([
            ('company_ids', 'in', cls.company.id),
            ('account_type', 'in', ('income', 'income_other')),
        ], limit=1)
        cls.expense_account = cls.accounts.search([
            ('company_ids', 'in', cls.company.id),
            ('account_type', '=', 'expense'),
        ], limit=1)
        cls.journal = cls.env['account.journal'].search([
            ('company_id', '=', cls.company.id), ('type', '=', 'sale'),
        ], limit=1)
        if not cls.income_account or not cls.expense_account or not cls.journal:
            raise SkipTest('A COP company with a chart and sales journal is required for invoice rounding tests.')

        cls.rounding_rule = cls.env['account.cash.rounding'].with_company(cls.company).create({
            'name': 'Test COP nearest peso',
            'rounding': 1.0,
            'rounding_method': 'HALF-UP',
            'strategy': 'add_invoice_line',
            'profit_account_id': cls.income_account.id,
            'loss_account_id': cls.expense_account.id,
        })
        cls.company.write({
            'co_invoice_rounding_enabled': True,
            'co_invoice_cash_rounding_id': cls.rounding_rule.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Rounding Test Partner',
            'company_id': False,
            'country_id': cls.env.ref('base.co').id,
        })
        cls.product = cls.env['product.product'].with_company(cls.company).create({
            'name': 'Rounding Test Product',
            'company_id': False,
            'property_account_income_id': cls.income_account.id,
            'taxes_id': [Command.clear()],
        })

    def _create_invoice(self, amount, move_type='out_invoice', quantity=1.0, currency=None, taxes=None, post=True):
        invoice = self.env['account.move'].with_company(self.company).create({
            'company_id': self.company.id,
            'move_type': move_type,
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'currency_id': (currency or self.company.currency_id).id,
            'invoice_date': '2026-10-26',
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': quantity,
                'price_unit': amount / quantity,
                'account_id': self.income_account.id,
                'tax_ids': [Command.set((taxes or self.env['account.tax']).ids)],
            })],
        })
        if post:
            invoice.action_post()
        return invoice

    def test_decimal_half_up_examples_and_negative_credit_notes(self):
        for source, expected in (
            ('21450.49', '21450.00'),
            ('21450.50', '21451.00'),
            ('21450.75', '21451.00'),
            ('21450.99', '21451.00'),
            ('21450.00', '21450.00'),
            ('-21450.49', '-21450.00'),
            ('-21450.50', '-21451.00'),
            ('-21450.99', '-21451.00'),
        ):
            actual = self.rounding_rule.round(float(source))
            self.assertEqual(Decimal(str(actual)), Decimal(expected))
        self.assertEqual(self.rounding_rule.compute_difference(self.company.currency_id, -21450.49), 0.49)
        self.assertEqual(self.rounding_rule.compute_difference(self.company.currency_id, -21450.50), -0.50)

    def test_document_rounding_line_preserves_product_subtotal_and_balances_entry(self):
        invoice = self._create_invoice(21450.49)
        self.assertEqual(invoice.amount_total, 21450.00)
        self.assertEqual(invoice.amount_untaxed, 21450.00)
        self.assertEqual(invoice.amount_tax, 0.0)
        self.assertEqual(invoice.invoice_line_ids.price_subtotal, 21450.49)
        self.assertEqual(invoice.invoice_line_ids.price_total, 21450.49)
        self.assertEqual(len(invoice.line_ids.filtered(lambda line: line.display_type == 'rounding')), 1)
        self.assertEqual(invoice.amount_residual, invoice.amount_total)
        self.assertTrue(self.company.currency_id.is_zero(sum(invoice.line_ids.mapped('balance'))))

    def test_round_once_on_document_not_independently_per_line(self):
        invoice = self.env['account.move'].with_company(self.company).create({
            'company_id': self.company.id,
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'currency_id': self.company.currency_id.id,
            'invoice_date': '2026-10-26',
            'invoice_line_ids': [
                Command.create({'product_id': self.product.id, 'quantity': 1, 'price_unit': 10725.25, 'account_id': self.income_account.id, 'tax_ids': [Command.clear()]}),
                Command.create({'product_id': self.product.id, 'quantity': 1, 'price_unit': 10725.25, 'account_id': self.income_account.id, 'tax_ids': [Command.clear()]}),
            ],
        })
        invoice.action_post()
        self.assertEqual(invoice.amount_total, 21451.00)
        self.assertEqual(invoice.invoice_line_ids.mapped('price_subtotal'), [10725.25, 10725.25])
        self.assertEqual(invoice.line_ids.filtered(lambda line: line.display_type == 'rounding').amount_currency, -0.5)

    def test_vat_and_withholding_are_not_rewritten_to_force_rounding(self):
        vat = self.env['account.tax'].with_company(self.company).search([
            ('company_id', '=', self.company.id), ('type_tax_use', '=', 'sale'), ('amount', '=', 19),
        ], limit=1)
        retention = self.env['account.tax'].with_company(self.company).search([
            ('company_id', '=', self.company.id),
            ('type_tax_use', '=', 'sale'),
            ('l10n_co_edi_type.retention', '=', True),
        ], limit=1)
        if not vat or not retention:
            raise SkipTest('Colombian VAT and withholding taxes are required for this test.')
        invoice = self._create_invoice(21450.49, taxes=vat | retention)
        self.assertEqual(invoice.invoice_line_ids.price_subtotal, 21450.49)
        self.assertTrue(invoice.line_ids.filtered(lambda line: line.display_type == 'rounding'))
        tax_lines = invoice.line_ids.filtered(lambda line: line.display_type == 'tax')
        self.assertTrue(tax_lines.filtered(lambda line: line.tax_line_id == vat))
        self.assertTrue(tax_lines.filtered(lambda line: line.tax_line_id == retention))
        self.assertTrue(self.company.currency_id.is_zero(sum(invoice.line_ids.mapped('balance'))))

    def test_ubl_payable_rounding_amount_matches_document_total(self):
        invoice = self._create_invoice(21450.49, post=False)
        rounding_line = invoice.line_ids.filtered(lambda line: line.display_type == 'rounding')
        product_total = sum(invoice.invoice_line_ids.mapped('price_subtotal'))
        rounding_base = invoice._prepare_cash_rounding_base_line_for_taxes_computation(rounding_line)
        self.env['account.tax']._add_tax_details_in_base_line(rounding_base, self.company)
        payable_rounding = rounding_base['tax_details']['raw_total_excluded_currency']
        vals = {
            'invoice': invoice,
            'document_type': 'invoice',
            'currency_suffix': '_currency',
            'currency_name': 'COP',
            'currency_dp': 2,
            'total_lines_currency': product_total,
            'total_lines': product_total,
            'total_allowance_currency': 0.0,
            'total_charge_currency': 0.0,
            'tax_exclusive_amount_currency': product_total,
            'total_tax_amount_currency': 0.0,
            'total_tax_amount': 0.0,
            'tax_inclusive_amount_currency': product_total,
            'tax_inclusive_amount': product_total,
            'cash_rounding_base_amount_currency': payable_rounding,
            'cash_rounding_base_amount': payable_rounding,
            'prepayments': [],
        }
        document = {}
        self.env['account.edi.xml.ubl_dian']._add_invoice_monetary_total_nodes(document, vals)
        total = document['cac:LegalMonetaryTotal']
        self.assertEqual(
            Decimal(total['cbc:LineExtensionAmount']['_text']).quantize(Decimal('0.01')),
            Decimal('21450.49'),
        )
        self.assertEqual(
            Decimal(total['cbc:PayableAmount']['_text']).quantize(Decimal('0.01')),
            Decimal('21450.00'),
        )
        self.assertEqual(
            Decimal(total['cbc:PayableAmount']['_text']).quantize(Decimal('0.01')),
            (Decimal(total['cbc:TaxInclusiveAmount']['_text']) + Decimal(total['cbc:PayableRoundingAmount']['_text'])).quantize(Decimal('0.01')),
        )

    def test_foreign_currency_other_companies_and_gallon_quantity(self):
        usd = self.env.ref('base.USD')
        foreign = self._create_invoice(21450.50, currency=usd)
        self.assertFalse(foreign.invoice_cash_rounding_id)

        gallons = self._create_invoice(21450.0, quantity=1.5)
        self.assertEqual(gallons.invoice_line_ids.quantity, 1.5)
        self.assertEqual(gallons.invoice_line_ids.price_subtotal, 21450.0)
        self.assertEqual(gallons.amount_total, 21450.0)

        three_decimal_gallons = self._create_invoice(21464.3, quantity=1.501)
        self.assertEqual(three_decimal_gallons.invoice_line_ids.quantity, 1.501)
        self.assertEqual(three_decimal_gallons.invoice_line_ids.price_unit, 14300.0)
        self.assertEqual(three_decimal_gallons.invoice_line_ids.price_subtotal, 21464.3)
        self.assertEqual(three_decimal_gallons.amount_total, 21464.0)

        other_company = self.env['res.company'].search([
            ('id', '!=', self.company.id), ('currency_id.name', '=', 'COP'),
        ], limit=1)
        if other_company:
            other_rule = self.env['account.move']._co_invoice_rounding_rule(
                other_company, other_company.currency_id, 'out_invoice'
            )
            self.assertFalse(other_rule)

    def test_posted_invoice_does_not_change_when_company_setting_is_disabled(self):
        invoice = self._create_invoice(21450.49)
        before = (invoice.amount_total, invoice.amount_residual, invoice.line_ids.mapped('balance'))
        self.company.co_invoice_rounding_enabled = False
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual((invoice.amount_total, invoice.amount_residual, invoice.line_ids.mapped('balance')), before)


