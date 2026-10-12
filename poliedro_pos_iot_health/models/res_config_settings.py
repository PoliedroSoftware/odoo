from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_poliedro_iot_health_enabled = fields.Boolean(
        related="pos_config_id.poliedro_iot_health_enabled",
        readonly=False,
    )
    pos_poliedro_iot_health_warn_before_validation = fields.Boolean(
        related="pos_config_id.poliedro_iot_health_warn_before_validation",
        readonly=False,
    )
