from odoo import _, api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.onchange("pos_conf_id")
    def _onchange_pos_conf_id(self):
        """Keep the vendor validation while returning a translated warning."""
        if self.pos_conf_id and not self.has_group("point_of_sale.group_pos_user"):
            return {
                "warning": {
                    "title": _("Access Denied"),
                    "message": _(
                        "This user must be in the POS User group to set a POS "
                        "configuration."
                    ),
                }
            }
