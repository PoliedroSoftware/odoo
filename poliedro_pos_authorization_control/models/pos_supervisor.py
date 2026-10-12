import re

from werkzeug.security import check_password_hash, generate_password_hash

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class PoliedroPosSupervisor(models.Model):
    _name = "poliedro.pos.supervisor"
    _description = "Supervisor autorizado del POS"
    _order = "name"

    name = fields.Char(required=True)
    user_id = fields.Many2one("res.users", string="Usuario relacionado", required=True, ondelete="cascade")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    config_ids = fields.Many2many("pos.config", string="Puntos de venta")
    active = fields.Boolean(default=True)
    pin_hash = fields.Char(copy=False, groups="point_of_sale.group_pos_manager")
    pin = fields.Char(
        string="Nuevo PIN", compute="_compute_pin", inverse="_inverse_pin",
        groups="point_of_sale.group_pos_manager", help="Digite entre 4 y 10 números. El PIN se almacena cifrado."
    )

    _user_company_uniq = models.Constraint(
        "UNIQUE(user_id, company_id)", "El usuario ya está configurado como supervisor en esta compañía."
    )

    @api.depends("pin_hash")
    def _compute_pin(self):
        for record in self:
            record.pin = False

    def _inverse_pin(self):
        for record in self:
            if not record.pin:
                continue
            if not re.fullmatch(r"\d{4,10}", record.pin):
                raise ValidationError(_("El PIN debe contener entre 4 y 10 números."))
            record.pin_hash = generate_password_hash(record.pin)

    @api.model
    def verify_pin(self, pin, config_id):
        if not self.env.user.has_group("point_of_sale.group_pos_user"):
            raise AccessError(_("No tiene permisos para operar el punto de venta."))
        if not isinstance(pin, str) or not re.fullmatch(r"\d{4,10}", pin):
            return {"authorized": False}
        config = self.env["pos.config"].browse(int(config_id)).exists()
        if not config or config.company_id not in self.env.companies:
            raise AccessError(_("El punto de venta no está disponible."))
        supervisors = self.sudo().search([
            ("active", "=", True), ("company_id", "=", config.company_id.id),
            "|", ("config_ids", "=", False), ("config_ids", "in", config.id),
        ])
        for supervisor in supervisors:
            if supervisor.pin_hash and check_password_hash(supervisor.pin_hash, pin):
                return {
                    "authorized": True,
                    "supervisor_id": supervisor.user_id.id,
                    "supervisor_name": supervisor.name,
                }
        return {"authorized": False}
