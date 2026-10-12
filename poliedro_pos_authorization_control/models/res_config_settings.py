from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_poliedro_authorization_enabled = fields.Boolean(related="pos_config_id.poliedro_authorization_enabled", readonly=False)
    pos_poliedro_auth_refund = fields.Boolean(related="pos_config_id.poliedro_auth_refund", readonly=False)
    pos_poliedro_auth_price_change = fields.Boolean(related="pos_config_id.poliedro_auth_price_change", readonly=False)
    pos_poliedro_auth_line_delete = fields.Boolean(related="pos_config_id.poliedro_auth_line_delete", readonly=False)
    pos_poliedro_auth_cashbox = fields.Boolean(related="pos_config_id.poliedro_auth_cashbox", readonly=False)
    pos_poliedro_auth_discount_threshold = fields.Float(related="pos_config_id.poliedro_auth_discount_threshold", readonly=False)
