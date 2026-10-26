from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    co_invoice_rounding_enabled = fields.Boolean(
        string='Round COP sales invoice totals to the nearest peso',
        default=False,
        help=(
            'Use the selected native cash rounding rule on new COP customer invoices and credit notes. '
            'Product line amounts and taxes remain calculated by Odoo; the difference is recorded as a '
            'separate, untaxed accounting rounding line.'
        ),
    )
    co_invoice_cash_rounding_id = fields.Many2one(
        'account.cash.rounding',
        string='Native cash rounding rule',
        check_company=False,
        help='Select a HALF-UP, 1.00 precision rule using the add-invoice-line strategy.',
    )

    @api.constrains('co_invoice_rounding_enabled', 'co_invoice_cash_rounding_id')
    def _check_co_invoice_rounding_configuration(self):
        for company in self:
            if not company.co_invoice_rounding_enabled:
                continue
            company._validate_co_invoice_rounding_configuration()

    def _validate_co_invoice_rounding_configuration(self):
        for company in self:
            if company.currency_id.name != 'COP' or company.account_fiscal_country_id.code != 'CO':
                raise ValidationError(_('Peso rounding can only be enabled for a Colombian company whose currency is COP.'))
            rounding = company.co_invoice_cash_rounding_id
            if not rounding:
                raise ValidationError(_('Select a native cash rounding rule before enabling peso rounding.'))
            if rounding.rounding != 1.0 or rounding.rounding_method != 'HALF-UP' or rounding.strategy != 'add_invoice_line':
                raise ValidationError(_(
                    'The Colombian peso rule must use precision 1.00, method HALF-UP, '
                    'and the Add a rounding line strategy.'
                ))
            company_rounding = rounding.with_company(company)
            if not company_rounding.profit_account_id or not company_rounding.loss_account_id:
                raise ValidationError(_(
                    'Configure both profit and loss accounts on the native cash rounding rule for this company.'
                ))
            if company_rounding.profit_account_id.account_type in ('asset_receivable', 'liability_payable'):
                raise ValidationError(_('The rounding profit account cannot be a receivable or payable account.'))
            if company_rounding.loss_account_id.account_type in ('asset_receivable', 'liability_payable'):
                raise ValidationError(_('The rounding loss account cannot be a receivable or payable account.'))
        return True

