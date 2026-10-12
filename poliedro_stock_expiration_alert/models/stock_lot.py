from datetime import timedelta

from odoo import api, fields, models, _


class StockLot(models.Model):
    _inherit = "stock.lot"

    poliedro_expiration_state = fields.Selection(
        [("no_date", "Sin fecha"), ("ok", "Vigente"), ("warning", "Próximo a vencer"),
         ("critical", "Crítico"), ("expired", "Vencido")],
        string="Estado de vencimiento", compute="_compute_poliedro_expiration_state"
    )
    poliedro_days_to_expiry = fields.Integer(
        string="Días para vencer", compute="_compute_poliedro_expiration_state"
    )
    poliedro_disposition = fields.Selection(
        [("available", "Disponible"), ("quarantine", "En cuarentena"),
         ("withdrawn", "Retirado"), ("loss", "Pérdida")],
        string="Disposición", default="available", required=True, tracking=True, index=True
    )
    poliedro_disposition_reason = fields.Text(string="Motivo de disposición", tracking=True)
    poliedro_disposition_date = fields.Datetime(string="Fecha de disposición", readonly=True)
    poliedro_disposition_user_id = fields.Many2one("res.users", string="Responsable", readonly=True)

    @api.depends("expiration_date")
    def _compute_poliedro_expiration_state(self):
        now = fields.Datetime.now()
        for lot in self:
            if not lot.expiration_date:
                lot.poliedro_expiration_state = "no_date"
                lot.poliedro_days_to_expiry = 0
                continue
            seconds = (lot.expiration_date - now).total_seconds()
            days = int(seconds // 86400) if seconds >= 0 else -int(abs(seconds) // 86400) - 1
            lot.poliedro_days_to_expiry = days
            if seconds < 0:
                lot.poliedro_expiration_state = "expired"
            elif days <= 7:
                lot.poliedro_expiration_state = "critical"
            elif days <= 30:
                lot.poliedro_expiration_state = "warning"
            else:
                lot.poliedro_expiration_state = "ok"

    def action_poliedro_quarantine(self):
        self.write({
            "poliedro_disposition": "quarantine",
            "poliedro_disposition_date": fields.Datetime.now(),
            "poliedro_disposition_user_id": self.env.user.id,
        })
        return True

    def action_poliedro_release(self):
        self.write({
            "poliedro_disposition": "available",
            "poliedro_disposition_date": fields.Datetime.now(),
            "poliedro_disposition_user_id": self.env.user.id,
        })
        return True

    def action_poliedro_withdraw_stock(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Retirar mercancía vencida"),
            "res_model": "stock.scrap",
            "view_mode": "form",
            "view_id": self.env.ref("stock.stock_scrap_form_view").id,
            "target": "current",
            "context": {
                "default_product_id": self.product_id.id,
                "default_lot_id": self.id,
                "default_location_id": self.location_id.id,
                "default_scrap_qty": self.product_qty,
                "default_origin": _("Retiro por vencimiento: %s", self.name),
                "default_poliedro_expiration_action": "withdrawn",
            },
        }
