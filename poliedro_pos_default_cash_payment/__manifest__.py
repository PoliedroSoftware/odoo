{
    "name": "Poliedro POS Default Cash Payment",
    "summary": "Selecciona efectivo automáticamente al abrir el cobro del POS",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "poliedro_pos_scanner_layout"],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_default_cash_payment/static/src/js/payment_screen.js",
        ],
    },
    "installable": True,
    "application": False,
}
