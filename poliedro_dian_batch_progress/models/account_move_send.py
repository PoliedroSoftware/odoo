from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _generate_and_send_invoices_post_commit(self, moves, **kwargs):
        dian_moves = moves.filtered(
            lambda move: move.move_type in ("out_invoice", "out_refund")
            and move.state == "posted"
        )
        if dian_moves:
            self.env["poliedro.dian.send.batch"].sudo().create({
                "company_id": dian_moves[0].company_id.id,
                "move_ids": [(6, 0, dian_moves.ids)],
            })
        return super()._generate_and_send_invoices_post_commit(moves, **kwargs)
