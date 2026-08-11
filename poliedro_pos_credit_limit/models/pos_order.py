from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class PosOrder(models.Model):
    _inherit = "pos.order"

    poliedro_credit_limit_snapshot = fields.Float(copy=False)
    poliedro_credit_used_before_snapshot = fields.Float(copy=False)
    poliedro_credit_payment_snapshot = fields.Float(copy=False)
    poliedro_credit_available_after_snapshot = fields.Float(copy=False)

    @api.model
    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        result = super()._process_payment_lines(pos_order, order, pos_session, draft)
        order._validate_poliedro_pos_credit_limit()
        return result

    def _validate_poliedro_pos_credit_limit(self):
        self.ensure_one()
        credit_payments = self.payment_ids.filtered(
            lambda payment: payment.payment_method_id.type == "pay_later"
        )
        credit_amount = sum(credit_payments.mapped("amount"))
        if credit_amount <= 0.0:
            self.write({
                "poliedro_credit_limit_snapshot": 0.0,
                "poliedro_credit_used_before_snapshot": 0.0,
                "poliedro_credit_payment_snapshot": 0.0,
                "poliedro_credit_available_after_snapshot": 0.0,
            })
            return

        if not self.partner_id:
            raise ValidationError(_("A customer is required to use Customer Account in the POS."))

        company = self.company_id
        company_currency = company.currency_id
        if self.currency_id != company_currency:
            credit_amount = self.currency_id._convert(
                credit_amount,
                company_currency,
                company,
                fields.Date.to_date(self.date_order),
            )

        commercial_partner = self.partner_id.commercial_partner_id
        self.env.cr.execute(
            "SELECT id FROM res_partner WHERE id = %s FOR UPDATE",
            [commercial_partner.id],
        )
        info = self.partner_id._get_pos_credit_info_map(
            company,
            exclude_order_ids=self.ids,
        )[self.partner_id.id]

        if info["is_limited"] and float_compare(
            credit_amount,
            info["available_credit"],
            precision_rounding=company_currency.rounding,
        ) > 0:
            raise ValidationError(_(
                "The customer-account payment of %(payment)s exceeds the available credit of %(available)s for %(partner)s.",
                payment=company_currency.format(credit_amount),
                available=company_currency.format(info["available_credit"]),
                partner=commercial_partner.display_name,
            ))

        self.write({
            "poliedro_credit_limit_snapshot": info["credit_limit"],
            "poliedro_credit_used_before_snapshot": info["used_credit"],
            "poliedro_credit_payment_snapshot": credit_amount,
            "poliedro_credit_available_after_snapshot": (
                max(info["available_credit"] - credit_amount, 0.0)
                if info["is_limited"]
                else 0.0
            ),
        })
