from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    invoice_header_banner_image = fields.Image(
        string="Invoice header banner",
        help="Optional wide brand image shown in the native customer invoice PDF.",
    )
    invoice_tagline = fields.Char(
        string="Invoice tagline",
        help="Optional short brand statement shown in the invoice header.",
    )
    invoice_value_1 = fields.Char(
        string="Brand message 1",
        help="Optional first short value statement shown in the invoice hero.",
    )
    invoice_value_2 = fields.Char(
        string="Brand message 2",
        help="Optional second short value statement shown in the invoice hero.",
    )
    invoice_value_3 = fields.Char(
        string="Brand message 3",
        help="Optional third short value statement shown in the invoice hero.",
    )
    invoice_footer_phrase = fields.Char(
        string="Invoice footer phrase",
        help="Optional short phrase shown in the invoice footer.",
    )
