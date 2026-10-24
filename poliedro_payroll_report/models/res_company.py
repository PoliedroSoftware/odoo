import re

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    poliedro_payroll_report_color = fields.Char(
        string="Color principal del desprendible",
        default="#155E63",
        help="Color hexadecimal (por ejemplo, #155E63) usado en el desprendible PDF.",
    )

    poliedro_payroll_banner = fields.Image(
        string="Banner del desprendible", max_width=2400, max_height=800,
        help="Cabecera completa del diseño anterior. Se conserva almacenada; el diseño horizontal usa el fondo independiente.",
    )
    poliedro_payroll_header_background = fields.Image(
        string="Fondo de la cabecera horizontal", max_width=2400, max_height=800,
        help="Fondo de la cabecera horizontal, sin logo ni datos variables. Sin imagen se usa el color principal. Solo se aplica a esta compañía.",
    )
    poliedro_payroll_tagline = fields.Char(string="Lema del desprendible")
    poliedro_payroll_footer_phrase = fields.Char(string="Frase del pie de nómina")

    def _get_poliedro_payroll_report_color(self):
        self.ensure_one()
        color = self.poliedro_payroll_report_color or "#155E63"
        return color if re.fullmatch(r"#[0-9A-Fa-f]{6}", color) else "#155E63"
