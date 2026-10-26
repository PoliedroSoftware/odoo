from decimal import Decimal

from odoo import models


class AccountEdiXmlUblDian(models.AbstractModel):
    _inherit = 'account.edi.xml.ubl_dian'

    def _add_invoice_monetary_total_nodes(self, document_node, vals):
        super()._add_invoice_monetary_total_nodes(document_node, vals)

        invoice = vals['invoice']
        if not (
            invoice.company_id.co_invoice_rounding_enabled
            and invoice.company_id.co_invoice_cash_rounding_id == invoice.invoice_cash_rounding_id
            and invoice.currency_id.name == 'COP'
            and invoice.move_type in ('out_invoice', 'out_refund')
        ):
            return

        rounding_amount = Decimal(str(vals.get('cash_rounding_base_amount_currency') or 0.0))
        if not rounding_amount:
            return

        monetary_total_tag = self._get_tags_for_document_type(vals)['monetary_total']
        monetary_total_node = document_node[monetary_total_tag]
        payable_amount = Decimal(str(vals['tax_inclusive_amount_currency'])) + rounding_amount
        monetary_total_node['cbc:PayableRoundingAmount'] = {
            '_text': self.format_float(float(rounding_amount), vals['currency_dp']),
            'currencyID': vals['currency_name'],
        }
        monetary_total_node['cbc:PayableAmount'] = {
            '_text': self.format_float(float(payable_amount), vals['currency_dp']),
            'currencyID': vals['currency_name'],
        }

