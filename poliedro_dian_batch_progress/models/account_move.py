from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _cron_account_move_send(self, job_count=1):
        """Send one queued move per scheduled run, without cron progress looping."""
        domain = [
            ("sending_data", "!=", False),
            ("state", "=", "posted"),
        ]
        move = self.search(
            domain,
            order="date asc, invoice_date asc, sequence_number asc, id asc",
            limit=1,
        ).try_lock_for_update()
        if move:
            self.env["account.move.send"]._generate_and_send_invoices(
                move,
                from_cron=True,
            )
