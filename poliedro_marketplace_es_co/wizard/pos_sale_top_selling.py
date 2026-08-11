from odoo import _, models
from odoo.exceptions import ValidationError


class PosSaleTopSelling(models.TransientModel):
    _inherit = "pos.sale.top.selling"

    def action_generate_report(self):
        """Translate validations emitted before the vendor report is generated."""
        self.ensure_one()
        if self.start_date > self.end_date:
            raise ValidationError(
                _("The End Date must be greater than the Start Date")
            )

        orders = self.env["pos.order"].search(
            [
                ("date_order", ">=", self.start_date),
                ("date_order", "<=", self.end_date),
                ("state", "in", ["paid", "invoiced", "done"]),
            ],
            limit=1,
        )
        if not orders:
            raise ValidationError(
                _("No POS orders found in the selected date range.")
            )
        return super().action_generate_report()
