from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    co_invoice_rounding_auto = fields.Boolean(copy=False, readonly=True)

    @api.model
    def _co_invoice_rounding_rule(self, company, currency, move_type):
        if (
            not company
            or not company.co_invoice_rounding_enabled
            or company.currency_id.name != 'COP'
            or currency != company.currency_id
            or move_type not in ('out_invoice', 'out_refund')
        ):
            return self.env['account.cash.rounding']
        rounding = company.co_invoice_cash_rounding_id
        if not rounding:
            return self.env['account.cash.rounding']
        company._validate_co_invoice_rounding_configuration()
        return rounding

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'invoice_cash_rounding_id' in vals and vals['invoice_cash_rounding_id']:
                continue
            company = self.env['res.company'].browse(vals.get('company_id') or self.env.company.id)
            currency = self.env['res.currency'].browse(vals.get('currency_id') or company.currency_id.id)
            rounding = self._co_invoice_rounding_rule(company, currency, vals.get('move_type', 'entry'))
            if rounding:
                vals['invoice_cash_rounding_id'] = rounding.id
                vals['co_invoice_rounding_auto'] = True
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if 'invoice_cash_rounding_id' in vals and not self.env.context.get('co_invoice_rounding_internal_sync'):
            vals['co_invoice_rounding_auto'] = False
        result = super().write(vals)

        changed_scope = {'company_id', 'currency_id', 'move_type'} & vals.keys()
        if changed_scope and not self.env.context.get('co_invoice_rounding_internal_sync'):
            for move in self.filtered(lambda record: record.state == 'draft' and record.co_invoice_rounding_auto):
                rounding = self._co_invoice_rounding_rule(move.company_id, move.currency_id, move.move_type)
                if move.invoice_cash_rounding_id != rounding:
                    super(AccountMove, move.with_context(co_invoice_rounding_internal_sync=True)).write({
                        'invoice_cash_rounding_id': rounding.id or False,
                        'co_invoice_rounding_auto': bool(rounding),
                    })
        return result

