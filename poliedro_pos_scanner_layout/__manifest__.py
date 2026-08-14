{
    "name": "Poliedro POS Scanner Layout",
    "summary": "Vista de caja profesional orientada a lectores de códigos de barras",
    "version": "19.0.1.5.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_scanner_layout/static/src/js/pos_order_line.js",
            "poliedro_pos_scanner_layout/static/src/js/product_screen.js",
            "poliedro_pos_scanner_layout/static/src/xml/product_screen.xml",
            "poliedro_pos_scanner_layout/static/src/scss/scanner_layout.scss",
        ],
    },
    "installable": True,
    "application": False,
}
