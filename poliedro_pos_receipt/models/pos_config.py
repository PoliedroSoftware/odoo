from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    # pos.config uses the generic POS loading mixin. Keep the standard POS
    # payload explicit when extending it so the frontend still receives the
    # company, currency, tax and pricing fields required by the price engine.
    _POLIEDRO_POS_FIELDS = [
        "id", "display_name", "access_token", "name", "printer_ids",
        "is_order_printer", "is_installed_account_accountant", "picking_type_id",
        "journal_id", "invoice_journal_id", "currency_id", "iface_cashdrawer",
        "iface_electronic_scale", "iface_print_via_proxy", "iface_scan_via_proxy",
        "iface_big_scrollbars", "iface_print_auto", "iface_print_skip_screen",
        "iface_tax_included", "iface_available_categ_ids", "customer_display_bg_img",
        "customer_display_bg_img_name", "restrict_price_control",
        "is_margins_costs_accessible_to_every_user", "cash_control",
        "set_maximum_difference", "receipt_header", "receipt_footer", "basic_receipt",
        "proxy_ip", "active", "uuid", "session_ids", "current_session_id",
        "current_session_state", "number_of_rescue_session", "last_session_closing_cash",
        "last_session_closing_date", "pos_session_username", "pos_session_state",
        "pos_session_duration", "pricelist_id", "available_pricelist_ids",
        "company_id", "group_pos_manager_id", "group_pos_user_id", "iface_tipproduct",
        "tip_product_id", "fiscal_position_ids", "default_fiscal_position_id",
        "default_bill_ids", "use_pricelist", "use_presets", "default_preset_id",
        "available_preset_ids", "tax_regime_selection", "limit_categories",
        "module_pos_restaurant", "module_pos_avatax", "module_pos_discount",
        "module_pos_appointment", "is_posbox", "is_header_or_footer", "module_pos_hr",
        "amount_authorized_diff", "payment_method_ids", "company_has_template",
        "current_user_id", "other_devices", "rounding_method", "cash_rounding",
        "only_round_cash_method", "has_active_session", "manual_discount", "ship_later",
        "warehouse_id", "route_id", "picking_policy", "auto_validate_terminal_payment",
        "trusted_config_ids", "show_product_images", "show_category_images", "note_ids",
        "module_pos_sms", "is_closing_entry_by_product", "order_edit_tracking",
        "last_data_change", "fallback_nomenclature_id", "create_date", "write_date",
        "epson_printer_ip", "use_fast_payment", "fast_payment_method_ids",
    ]

    poliedro_receipt_title = fields.Char(
        string="Título del recibo Poliedro",
        default="POLIEDRO SOFTWARE",
        help="Título que se muestra en el recibo de este punto de venta.",
    )
    poliedro_receipt_subtitle = fields.Char(
        string="Subtítulo del recibo",
        default="Comprobante de venta",
    )
    poliedro_receipt_footer = fields.Text(
        string="Mensaje final Poliedro",
        default="Gracias por su compra",
    )

    def _load_pos_data_fields(self, config):
        return self._POLIEDRO_POS_FIELDS + [
            "poliedro_receipt_title",
            "poliedro_receipt_subtitle",
            "poliedro_receipt_footer",
        ]
