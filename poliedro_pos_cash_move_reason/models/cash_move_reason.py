from odoo import api, fields, models


class PoliedroPosCashMoveReason(models.Model):
    _name = "poliedro.pos.cash.move.reason"
    _description = "Motivo de movimiento de efectivo"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    direction = fields.Selection(
        [("in", "Entrada"), ("out", "Salida"), ("both", "Entrada y salida")],
        required=True, default="both",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    config_ids = fields.Many2many("pos.config", string="Puntos de venta")

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)", "El código del motivo debe ser único por compañía."
    )

    @api.model
    def get_pos_reasons(self, direction, config_id):
        config = self.env["pos.config"].browse(int(config_id)).exists()
        domain = [
            ("active", "=", True),
            ("company_id", "=", config.company_id.id),
            ("direction", "in", [direction, "both"]),
            "|", ("config_ids", "=", False), ("config_ids", "in", config.id),
        ]
        return self.sudo().search_read(domain, ["name", "code"], order="sequence, name")
