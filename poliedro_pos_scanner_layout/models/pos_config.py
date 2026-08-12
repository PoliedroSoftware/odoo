from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    poliedro_scanner_layout_default = fields.Boolean(
        string="Scanner layout by default",
        default=True,
        help="Open the Point of Sale with the full-screen scanner-oriented order view.",
    )

    def _load_pos_data_fields(self, config):
        fields_to_load = super()._load_pos_data_fields(config)
        return [*fields_to_load, "poliedro_scanner_layout_default"]
