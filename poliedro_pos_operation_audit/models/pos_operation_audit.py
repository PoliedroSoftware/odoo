import json

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class PoliedroPosOperationAudit(models.Model):
    _name = "poliedro.pos.operation.audit"
    _description = "Auditoría de operaciones sensibles del POS"
    _order = "operation_datetime desc, id desc"

    operation_datetime = fields.Datetime(
        string="Fecha y hora", required=True, default=fields.Datetime.now, index=True
    )
    action = fields.Selection(
        selection=[
            ("line_delete", "Eliminación de producto"),
            ("order_cancel", "Anulación de venta"),
            ("refund", "Devolución"),
            ("price_change", "Cambio de precio"),
            ("discount", "Descuento"),
            ("cashbox_open", "Apertura de cajón sin venta"),
            ("cash_in", "Entrada de efectivo"),
            ("cash_out", "Salida de efectivo"),
        ],
        string="Operación",
        required=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    config_id = fields.Many2one("pos.config", string="Punto de venta", index=True)
    session_id = fields.Many2one("pos.session", string="Sesión", index=True)
    order_id = fields.Many2one("pos.order", string="Orden", index=True, ondelete="set null")
    order_reference = fields.Char(string="Referencia", index=True)
    product_id = fields.Many2one("product.product", string="Producto", index=True)
    user_id = fields.Many2one(
        "res.users", string="Usuario", required=True, default=lambda self: self.env.user, index=True
    )
    cashier_name = fields.Char(string="Cajero")
    supervisor_id = fields.Many2one("res.users", string="Supervisor", index=True)
    supervisor_name = fields.Char(string="Supervisor autorizado")
    reason = fields.Text(string="Motivo")
    previous_value = fields.Char(string="Valor anterior")
    new_value = fields.Char(string="Valor nuevo")
    amount = fields.Monetary(string="Importe", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=True
    )
    payload_json = fields.Text(string="Datos técnicos", readonly=True)

    @api.model
    def log_pos_action(self, payload):
        if not self.env.user.has_group("point_of_sale.group_pos_user"):
            raise AccessError(_("No tiene permisos para registrar operaciones del POS."))
        if not isinstance(payload, dict):
            raise ValidationError(_("La información de auditoría no es válida."))
        allowed_actions = dict(self._fields["action"].selection)
        action = payload.get("action")
        if action not in allowed_actions:
            raise ValidationError(_("La operación de auditoría no es válida."))

        def existing(model, value):
            if not value:
                return False
            record = self.env[model].browse(int(value)).exists()
            return record.id if record else False

        session_id = existing("pos.session", payload.get("session_id"))
        config_id = existing("pos.config", payload.get("config_id"))
        order_id = existing("pos.order", payload.get("order_id"))
        product_id = existing("product.product", payload.get("product_id"))
        supervisor_id = existing("res.users", payload.get("supervisor_id"))
        company = self.env.company
        if config_id:
            company = self.env["pos.config"].browse(config_id).company_id

        values = {
            "action": action,
            "company_id": company.id,
            "config_id": config_id,
            "session_id": session_id,
            "order_id": order_id,
            "order_reference": str(payload.get("order_reference") or "")[:128],
            "product_id": product_id,
            "user_id": self.env.user.id,
            "cashier_name": str(payload.get("cashier_name") or self.env.user.name)[:128],
            "supervisor_id": supervisor_id,
            "supervisor_name": str(payload.get("supervisor_name") or "")[:128],
            "reason": str(payload.get("reason") or "")[:2000],
            "previous_value": str(payload.get("previous_value") or "")[:256],
            "new_value": str(payload.get("new_value") or "")[:256],
            "amount": float(payload.get("amount") or 0),
            "payload_json": json.dumps(payload, ensure_ascii=False, default=str),
        }
        return self.sudo().create(values).id
