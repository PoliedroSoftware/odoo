{
    "name": "Poliedro POS Management Dashboard",
    "summary": "Tablero gerencial de ventas, margen, descuentos, caja y rotación",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "stock", "poliedro_pos_operation_audit"],
    "data": ["views/pos_management_dashboard_views.xml"],
    "assets": {
        "web.assets_backend": [
            "poliedro_pos_management_dashboard/static/src/js/dashboard.js",
            "poliedro_pos_management_dashboard/static/src/xml/dashboard.xml",
            "poliedro_pos_management_dashboard/static/src/scss/dashboard.scss",
        ],
    },
    "installable": True,
    "application": False,
}
