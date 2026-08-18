from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    poliedro_einvoice_webhook_url = fields.Char(
        string="URL del webhook",
        config_parameter="poliedro_pos_einvoice_webhook.url",
    )
    poliedro_einvoice_webhook_token = fields.Char(
        string="Token Bearer",
        config_parameter="poliedro_pos_einvoice_webhook.token",
    )
    poliedro_einvoice_webhook_secret = fields.Char(
        string="Secreto de firma",
        config_parameter="poliedro_pos_einvoice_webhook.secret",
    )
    poliedro_einvoice_webhook_timeout = fields.Integer(
        string="Tiempo máximo de espera",
        config_parameter="poliedro_pos_einvoice_webhook.timeout",
        default=10,
    )
