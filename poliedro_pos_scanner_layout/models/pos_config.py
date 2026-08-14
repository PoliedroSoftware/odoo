from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    poliedro_scanner_layout_default = fields.Boolean(
        string="Scanner layout by default",
        default=True,
        help="Open the Point of Sale with the full-screen scanner-oriented order view.",
    )
    poliedro_scanner_show_stock = fields.Boolean(
        string="Show stock in scanner layout",
        default=True,
        help="Display the available inventory of each product in the scanner order detail.",
    )

    def _load_pos_data_fields(self, config):
        fields_to_load = super()._load_pos_data_fields(config)
        return [*fields_to_load, "poliedro_scanner_layout_default", "poliedro_scanner_show_stock"]
