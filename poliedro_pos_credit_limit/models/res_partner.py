from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = "res.partner"

    pos_credit_limit_enabled = fields.Boolean(
        compute="_compute_pos_credit_metrics",
        string="POS Credit Limit Enabled",
    )
    pos_credit_limit_amount = fields.Float(
        compute="_compute_pos_credit_metrics",
        string="POS Credit Limit",
    )
    pos_credit_used_amount = fields.Float(
        compute="_compute_pos_credit_metrics",
        string="POS Credit Used",
    )
    pos_credit_available_amount = fields.Float(
        compute="_compute_pos_credit_metrics",
        string="POS Credit Available",
    )

    @api.model
    def _load_pos_data_fields(self, config):
        fields_to_load = super()._load_pos_data_fields(config)
        return fields_to_load + [
            "pos_credit_limit_enabled",
            "pos_credit_limit_amount",
            "pos_credit_used_amount",
            "pos_credit_available_amount",
        ]

    @api.depends_context("company")
    def _compute_pos_credit_metrics(self):
        info_by_partner = self._get_pos_credit_info_map(self.env.company)
        for partner in self:
            info = info_by_partner.get(partner.id, {})
            partner.pos_credit_limit_enabled = info.get("is_limited", False)
            partner.pos_credit_limit_amount = info.get("credit_limit", 0.0)
            partner.pos_credit_used_amount = info.get("used_credit", 0.0)
            partner.pos_credit_available_amount = info.get("available_credit", 0.0)

    def _get_pos_credit_info_map(self, company, exclude_order_ids=None):
        """Return authoritative credit information in the company currency.

        Native accounting credit does not include customer-account payments from
        open POS sessions until their accounting entry is posted. Those payments
        are therefore added as reserved credit here.
        """
        partners = self.exists()
        if not partners:
            return {}

        company = company.exists()
        commercial_partners = partners.mapped("commercial_partner_id").sudo().with_company(company)
        commercial_ids = commercial_partners.ids
        pending_by_partner = defaultdict(float)
        excluded_ids = [order_id for order_id in (exclude_order_ids or []) if order_id]

        payment_domain = [
            # ``pos.payment.method.type`` is computed and cannot be used in a
            # SQL domain. A payment method without a cash/bank journal is the
            # native Customer Account (pay_later) method.
            ("payment_method_id.journal_id", "=", False),
            ("pos_order_id.partner_id.commercial_partner_id", "in", commercial_ids),
            ("pos_order_id.company_id", "=", company.id),
            ("pos_order_id.state", "!=", "cancel"),
            ("pos_order_id.session_id.state", "!=", "closed"),
            ("pos_order_id.account_move", "=", False),
        ]
        if excluded_ids:
            payment_domain.append(("pos_order_id", "not in", excluded_ids))

        payments = self.env["pos.payment"].sudo().search(payment_domain)
        company_currency = company.currency_id
        for payment in payments:
            order = payment.pos_order_id
            amount = payment.amount
            if order.currency_id != company_currency:
                amount = order.currency_id._convert(
                    amount,
                    company_currency,
                    company,
                    fields.Date.to_date(order.date_order),
                )
            commercial_id = order.partner_id.commercial_partner_id.id
            pending_by_partner[commercial_id] += amount

        info_by_commercial = {}
        for commercial_partner in commercial_partners:
            credit_limit = commercial_partner.credit_limit or 0.0
            used_credit = (
                (commercial_partner.credit or 0.0)
                + (commercial_partner.credit_to_invoice or 0.0)
                + pending_by_partner[commercial_partner.id]
            )
            is_limited = bool(company.account_use_credit_limit and credit_limit > 0.0)
            available_credit = max(credit_limit - used_credit, 0.0) if is_limited else 0.0
            info_by_commercial[commercial_partner.id] = {
                "is_limited": is_limited,
                "feature_enabled": bool(company.account_use_credit_limit),
                "credit_limit": credit_limit,
                "used_credit": used_credit,
                "available_credit": available_credit,
                "currency_id": company_currency.id,
                "currency_symbol": company_currency.symbol,
            }

        return {
            partner.id: info_by_commercial[partner.commercial_partner_id.id]
            for partner in partners
        }

    @api.model
    def get_pos_credit_info(self, partner_id, company_id, exclude_order_id=False):
        if not self.env.user.has_group("point_of_sale.group_pos_user"):
            raise AccessError(_("Only Point of Sale users can consult POS credit information."))

        partner = self.browse(partner_id).exists()
        company = self.env["res.company"].browse(company_id).exists()
        if not partner or not company or company not in self.env.user.company_ids:
            raise AccessError(_("The customer or company is not available to this user."))

        info = partner._get_pos_credit_info_map(
            company,
            exclude_order_ids=[exclude_order_id] if exclude_order_id else None,
        )[partner.id]
        return info
