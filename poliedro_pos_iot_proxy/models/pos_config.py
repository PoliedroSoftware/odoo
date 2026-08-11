from odoo import api, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    @api.depends(
        "use_pricelist",
        "pricelist_id",
        "available_pricelist_ids",
        "payment_method_ids",
        "limit_categories",
        "iface_available_categ_ids",
        "module_pos_hr",
        "module_pos_discount",
        "iface_tipproduct",
        "default_preset_id",
        "module_pos_appointment",
        "proxy_ip",
        "is_posbox",
        "iface_electronic_scale",
        "iface_print_via_proxy",
        "iface_scan_via_proxy",
    )
    def _compute_local_data_integrity(self):
        """Invalidate POS cache whenever hardware proxy settings change."""
        return super()._compute_local_data_integrity()
