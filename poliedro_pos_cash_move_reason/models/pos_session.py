from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    poliedro_cash_move_reason_id = fields.Many2one(
        "poliedro.pos.cash.move.reason", string="Motivo de efectivo", ondelete="restrict"
    )


class PosSession(models.Model):
    _inherit = "pos.session"

    def _prepare_account_bank_statement_line_vals(self, session, sign, amount, reason, partner_id, extras):
        values = super()._prepare_account_bank_statement_line_vals(
            session, sign, amount, reason, partner_id, extras
        )
        reason_id = extras.get("poliedro_reason_id")
        if reason_id:
            catalog_reason = self.env["poliedro.pos.cash.move.reason"].browse(int(reason_id)).exists()
            if catalog_reason and catalog_reason.company_id == session.company_id:
                values["poliedro_cash_move_reason_id"] = catalog_reason.id
        return values

    def try_cash_in_out(self, _type, amount, reason, partner_id, extras):
        result = super().try_cash_in_out(_type, amount, reason, partner_id, extras)
        action = "cash_in" if _type == "in" else "cash_out"
        for session in self:
            self.env["poliedro.pos.operation.audit"].sudo().create({
                "action": action,
                "company_id": session.company_id.id,
                "config_id": session.config_id.id,
                "session_id": session.id,
                "user_id": self.env.user.id,
                "cashier_name": self.env.user.name,
                "reason": reason,
                "amount": amount,
            })
        return result
