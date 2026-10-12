{
    "name": "Poliedro POS Price Check",
    "summary": "Consulta precio, promoción y existencia sin agregar a la venta",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "poliedro_pos_scanner_layout"],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_price_check/static/src/js/price_check.js",
            "poliedro_pos_price_check/static/src/xml/price_check.xml",
            "poliedro_pos_price_check/static/src/scss/price_check.scss",
        ],
    },
    "installable": True,
    "application": False,
}
