from odoo import models

from .decimal_rounding import round_to_increment


class AccountCashRounding(models.Model):
    _inherit = 'account.cash.rounding'

    def _is_enabled_colombian_invoice_rounding_rule(self):
        return bool(self.env['res.company'].sudo().search_count([
            ('co_invoice_rounding_enabled', '=', True),
            ('co_invoice_cash_rounding_id', 'in', self.ids),
            ('currency_id.name', '=', 'COP'),
            ('account_fiscal_country_id.code', '=', 'CO'),
        ]))

    def compute_difference(self, currency, amount):
        self.ensure_one()
        if (
            self._is_enabled_colombian_invoice_rounding_rule()
            and currency.name == 'COP'
            and self.rounding == 1.0
            and self.rounding_method == 'HALF-UP'
        ):
            currency_quantum = currency.rounding
            amount_decimal = round_to_increment(amount, currency_quantum, currency_quantum)
            rounded_amount = round_to_increment(amount_decimal, self.rounding, currency_quantum)
            return float(rounded_amount - amount_decimal)
        return super().compute_difference(currency, amount)

