from odoo import fields, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    poliedro_expiration_action = fields.Selection(
        [("withdrawn", "Retiro por vencimiento"), ("loss", "Pérdida por vencimiento")],
        string="Tratamiento de vencimiento"
    )
    poliedro_expiration_note = fields.Text(string="Motivo detallado")

    def do_scrap(self):
        result = super().do_scrap()
        for scrap in self.filtered(lambda item: item.lot_id and item.poliedro_expiration_action):
            scrap.lot_id.write({
                "poliedro_disposition": scrap.poliedro_expiration_action,
                "poliedro_disposition_reason": scrap.poliedro_expiration_note or scrap.origin,
                "poliedro_disposition_date": fields.Datetime.now(),
                "poliedro_disposition_user_id": self.env.user.id,
            })
        return result
