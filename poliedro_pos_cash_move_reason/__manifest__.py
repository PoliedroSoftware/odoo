{
    "name": "Poliedro POS Cash Move Reason",
    "summary": "Motivos obligatorios y auditables para movimientos de efectivo",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "poliedro_pos_operation_audit", "poliedro_pos_cash_closing_receipt"],
    "data": [
        "security/ir.model.access.csv",
        "views/cash_move_reason_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_cash_move_reason/static/src/js/cash_move_popup.js",
            "poliedro_pos_cash_move_reason/static/src/xml/cash_move_popup.xml",
            "poliedro_pos_cash_move_reason/static/src/scss/cash_move_reason.scss",
        ],
    },
    "installable": True,
    "application": False,
}
