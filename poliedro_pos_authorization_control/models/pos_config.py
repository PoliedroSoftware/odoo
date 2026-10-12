from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    poliedro_authorization_enabled = fields.Boolean(string="Autorizaciones con PIN", default=False)
    poliedro_auth_refund = fields.Boolean(string="Autorizar devoluciones", default=True)
    poliedro_auth_price_change = fields.Boolean(string="Autorizar cambios de precio", default=True)
    poliedro_auth_line_delete = fields.Boolean(string="Autorizar eliminación de productos", default=True)
    poliedro_auth_cashbox = fields.Boolean(string="Autorizar apertura del cajón", default=True)
    poliedro_auth_discount_threshold = fields.Float(string="Descuento máximo sin autorización", default=10.0)

    def _load_pos_data_fields(self, config):
        return super()._load_pos_data_fields(config) + [
            "poliedro_authorization_enabled", "poliedro_auth_refund",
            "poliedro_auth_price_change", "poliedro_auth_line_delete",
            "poliedro_auth_cashbox", "poliedro_auth_discount_threshold",
        ]
