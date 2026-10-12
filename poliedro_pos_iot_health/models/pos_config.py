from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    poliedro_iot_health_enabled = fields.Boolean(
        string="Monitor de salud IoT",
        default=True,
        help="Muestra el estado de la impresora, la bascula y el cajon en la vista lector.",
    )
    poliedro_iot_health_warn_before_validation = fields.Boolean(
        string="Advertir antes de vender sin impresora",
        default=True,
        help="Solicita confirmacion si la impresion automatica esta configurada y la impresora no responde.",
    )

    def _load_pos_data_fields(self, config):
        fields_to_load = super()._load_pos_data_fields(config)
        return [
            *fields_to_load,
            "poliedro_iot_health_enabled",
            "poliedro_iot_health_warn_before_validation",
        ]
