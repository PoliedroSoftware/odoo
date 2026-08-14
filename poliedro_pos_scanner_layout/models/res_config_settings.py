from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_poliedro_scanner_layout_default = fields.Boolean(
        related="pos_config_id.poliedro_scanner_layout_default",
        readonly=False,
    )
    pos_poliedro_scanner_show_stock = fields.Boolean(
        related="pos_config_id.poliedro_scanner_show_stock",
        readonly=False,
    )
