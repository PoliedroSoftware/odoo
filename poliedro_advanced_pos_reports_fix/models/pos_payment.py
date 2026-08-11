from odoo import models


class PosPayment(models.Model):
    _inherit = "pos.payment"

    def get_payment_summary(self, order_ids):
        """Return payment totals grouped by method for the selected orders."""
        if not order_ids:
            return []

        grouped_payments = self._read_group(
            [("pos_order_id", "in", order_ids)],
            ["payment_method_id"],
            ["amount:sum"],
        )
        return [
            {
                "id": payment_method.id,
                "name": payment_method.display_name,
                "total": amount,
            }
            for payment_method, amount in grouped_payments
        ]
