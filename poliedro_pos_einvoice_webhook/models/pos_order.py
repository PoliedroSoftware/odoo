import hashlib
import hmac
import json
import logging
import uuid
from datetime import timezone
from urllib.parse import urlparse

import requests

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError


_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    poliedro_einvoice_state = fields.Selection(
        selection=[
            ("pending", "Pendiente"),
            ("queued", "Enviado a cola"),
            ("error", "Error"),
        ],
        string="Envío electrónico",
        default="pending",
        copy=False,
        readonly=True,
        index=True,
    )
    poliedro_einvoice_request_id = fields.Char(
        string="Identificador del envío",
        copy=False,
        readonly=True,
        index=True,
    )
    poliedro_einvoice_requested_at = fields.Datetime(
        string="Enviado a la cola el",
        copy=False,
        readonly=True,
    )
    poliedro_einvoice_attempts = fields.Integer(
        string="Intentos",
        copy=False,
        readonly=True,
    )
    poliedro_einvoice_last_response = fields.Text(
        string="Última respuesta",
        copy=False,
        readonly=True,
    )

    def action_poliedro_send_einvoice_webhook(self):
        if not self.env.user.has_group("point_of_sale.group_pos_manager"):
            raise AccessError(_("Solo un responsable del Punto de Venta puede realizar este envío."))

        orders = self.exists()
        if not orders:
            return False

        config = self._poliedro_einvoice_webhook_config()
        sent = 0
        skipped = 0
        failed = []

        for order in orders:
            if order.poliedro_einvoice_state == "queued":
                skipped += 1
                continue
            try:
                order._poliedro_send_einvoice_webhook(config)
                sent += 1
            except Exception as error:  # Continue sending the rest of the selected batch.
                message = str(error)[:1000]
                order.write(
                    {
                        "poliedro_einvoice_state": "error",
                        "poliedro_einvoice_attempts": order.poliedro_einvoice_attempts + 1,
                        "poliedro_einvoice_last_response": message,
                    }
                )
                failed.append(order.display_name)
                _logger.warning(
                    "Electronic invoice webhook failed for POS order %s: %s",
                    order.id,
                    message,
                )

        if failed:
            notification_type = "warning"
            title = _("Envío completado con novedades")
        else:
            notification_type = "success" if sent else "info"
            title = _("Órdenes enviadas a la cola")

        message_parts = [_('%(count)s enviada(s)', count=sent)]
        if skipped:
            message_parts.append(_('%(count)s ya estaba(n) enviada(s)', count=skipped))
        if failed:
            message_parts.append(
                _('%(count)s con error: %(orders)s', count=len(failed), orders=", ".join(failed))
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": ". ".join(message_parts),
                "type": notification_type,
                "sticky": bool(failed),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

    def _poliedro_einvoice_webhook_config(self):
        parameters = self.env["ir.config_parameter"].sudo()
        url = (parameters.get_param("poliedro_pos_einvoice_webhook.url") or "").strip()
        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise UserError(
                _("Configure una URL HTTP o HTTPS válida para el webhook de facturación electrónica.")
            )

        timeout_value = parameters.get_param("poliedro_pos_einvoice_webhook.timeout", "10")
        try:
            timeout = max(1, min(int(timeout_value), 60))
        except (TypeError, ValueError):
            timeout = 10

        return {
            "url": url,
            "token": parameters.get_param("poliedro_pos_einvoice_webhook.token") or "",
            "secret": parameters.get_param("poliedro_pos_einvoice_webhook.secret") or "",
            "timeout": timeout,
        }

    def _poliedro_send_einvoice_webhook(self, config):
        self.ensure_one()
        if self.state in {"draft", "cancel"}:
            raise UserError(
                _(
                    "La orden %(order)s debe estar pagada o registrada antes de enviarla.",
                    order=self.display_name,
                )
            )

        request_id = self.poliedro_einvoice_request_id or str(uuid.uuid4())
        payload = self._poliedro_einvoice_payload(request_id)
        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": "Poliedro-Odoo-POS/1.0",
            "Idempotency-Key": request_id,
            "X-Poliedro-Event": "pos.order.einvoice.requested",
        }
        if config["token"]:
            headers["Authorization"] = f"Bearer {config['token']}"
        if config["secret"]:
            signature = hmac.new(
                config["secret"].encode("utf-8"),
                body,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Poliedro-Signature"] = f"sha256={signature}"

        try:
            response = requests.post(
                config["url"],
                data=body,
                headers=headers,
                timeout=config["timeout"],
            )
            response.raise_for_status()
        except requests.RequestException as error:
            response_detail = getattr(error.response, "text", "") if error.response else ""
            detail = response_detail.strip()[:700]
            if detail:
                raise UserError(_("El webhook rechazó la orden: %s", detail)) from error
            raise UserError(_("No fue posible conectar con la cola: %s", error)) from error

        response_text = (response.text or "Aceptado por la cola").strip()[:1000]
        self.write(
            {
                "poliedro_einvoice_state": "queued",
                "poliedro_einvoice_request_id": request_id,
                "poliedro_einvoice_requested_at": fields.Datetime.now(),
                "poliedro_einvoice_attempts": self.poliedro_einvoice_attempts + 1,
                "poliedro_einvoice_last_response": response_text,
            }
        )
        return True

    def _poliedro_einvoice_payload(self, request_id):
        self.ensure_one()
        partner = self.partner_id
        company = self.company_id

        return {
            "event": "pos.order.einvoice.requested",
            "version": "1.0",
            "request_id": request_id,
            "source": {
                "system": "odoo",
                "database": self.env.cr.dbname,
                "company_id": company.id,
                "company_name": company.name,
                "company_vat": company.vat or None,
            },
            "order": {
                "id": self.id,
                "name": self.name,
                "reference": self.pos_reference or self.name,
                "date": self._poliedro_iso_datetime(self.date_order),
                "state": self.state,
                "point_of_sale": self.config_id.name,
                "session": self.session_id.name,
                "cashier": self.user_id.name,
                "currency": self.currency_id.name,
                "subtotal": self.amount_total - self.amount_tax,
                "tax": self.amount_tax,
                "total": self.amount_total,
                "paid": self.amount_paid,
                "change": self.amount_return,
                "odoo_invoice_requested": bool(self.to_invoice),
                "odoo_invoice_id": self.account_move.id or None,
            },
            "customer": self._poliedro_einvoice_partner_payload(partner),
            "lines": [self._poliedro_einvoice_line_payload(line) for line in self.lines],
            "payments": [
                {
                    "method": payment.payment_method_id.name,
                    "amount": payment.amount,
                    "date": self._poliedro_iso_datetime(payment.payment_date),
                }
                for payment in self.payment_ids
            ],
        }

    def _poliedro_einvoice_partner_payload(self, partner):
        if not partner:
            return {
                "id": None,
                "name": "Consumidor final",
                "consumer_final": True,
            }

        identification_type = None
        if "l10n_latam_identification_type_id" in partner._fields:
            identification_type = partner.l10n_latam_identification_type_id.name or None

        return {
            "id": partner.id,
            "name": partner.name,
            "consumer_final": False,
            "vat": partner.vat or None,
            "identification_type": identification_type,
            "email": partner.email or None,
            "phone": partner.phone or partner.mobile or None,
            "street": partner.street or None,
            "street2": partner.street2 or None,
            "city": partner.city or None,
            "state": partner.state_id.name or None,
            "country": partner.country_id.code or None,
            "zip": partner.zip or None,
        }

    def _poliedro_einvoice_line_payload(self, line):
        taxes = line.tax_ids_after_fiscal_position or line.tax_ids
        return {
            "id": line.id,
            "product_id": line.product_id.id,
            "sku": line.product_id.default_code or None,
            "barcode": line.product_id.barcode or None,
            "description": line.full_product_name or line.product_id.display_name,
            "quantity": line.qty,
            "unit_price": line.price_unit,
            "discount_percent": line.discount,
            "subtotal": line.price_subtotal,
            "total": line.price_subtotal_incl,
            "taxes": [
                {
                    "id": tax.id,
                    "name": tax.name,
                    "amount": tax.amount,
                    "amount_type": tax.amount_type,
                    "price_include": tax.price_include,
                }
                for tax in taxes
            ],
        }

    @staticmethod
    def _poliedro_iso_datetime(value):
        if not value:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
