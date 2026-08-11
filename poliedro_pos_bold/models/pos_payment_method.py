import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlencode

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    bold_merchant_id = fields.Char(
        string="Bold Merchant ID",
        copy=False,
        help="Identificador del comercio que aparece en el panel de Bold.",
    )

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [("bold", "Bold NEO (Applink)")]

    @api.model
    def _load_pos_data_fields(self, config):
        return super()._load_pos_data_fields(config) + ["bold_merchant_id"]

    @api.constrains("use_payment_terminal", "bold_merchant_id")
    def _check_bold_configuration(self):
        for payment_method in self:
            if payment_method.use_payment_terminal == "bold" and not payment_method.bold_merchant_id:
                raise ValidationError(_("Configure el Merchant ID de Bold para usar Applink."))

    def bold_create_applink(self, amount, reference, description=None):
        """Build a Bold NEO Applink without exposing configuration logic in the POS client."""
        self.ensure_one()
        if not self.env.user.has_group("point_of_sale.group_pos_user"):
            raise AccessError(_("No tiene permisos para iniciar pagos de Bold."))
        if self.use_payment_terminal != "bold":
            raise UserError(_("El metodo de pago no esta configurado para Bold NEO."))
        if not self.bold_merchant_id:
            raise UserError(_("Falta configurar el Merchant ID de Bold."))

        currency = self.journal_id.currency_id or self.company_id.currency_id
        if currency.name != "COP":
            raise UserError(_("Bold Applink solo puede utilizarse con pagos en COP."))

        try:
            amount_decimal = Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, TypeError, ValueError) as error:
            raise UserError(_("El valor del pago Bold no es valido.")) from error
        if amount_decimal <= 0:
            raise UserError(_("El valor del pago Bold debe ser mayor que cero."))

        clean_reference = re.sub(r"[^A-Za-z0-9_-]", "", reference or "")[:24]
        if not clean_reference:
            raise UserError(_("No fue posible generar la referencia del pago Bold."))

        clean_description = re.sub(r"[\r\n]+", " ", description or "Venta Odoo POS").strip()[:20]
        query = urlencode(
            {
                "action": "start_payment",
                "value_to_collect": str(amount_decimal),
                "merchant_id": self.bold_merchant_id.strip(),
                "reference": clean_reference,
                "description": clean_description or "Venta Odoo POS",
            }
        )
        return {
            "url": f"https://bold.co/deeplink?{query}",
            "reference": clean_reference,
            "amount": int(amount_decimal),
        }
