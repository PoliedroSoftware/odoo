{
    "name": "Poliedro POS Credit Limit",
    "summary": "Control estricto del cupo nativo en pagos POS a cuenta del cliente",
    "version": "19.0.1.0.1",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["account", "point_of_sale", "poliedro_pos_receipt"],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_credit_limit/static/src/js/payment_screen.js",
            "poliedro_pos_credit_limit/static/src/xml/payment_screen.xml",
            "poliedro_pos_credit_limit/static/src/xml/pos_receipt.xml",
            "poliedro_pos_credit_limit/static/src/scss/pos_credit_limit.scss",
        ],
    },
    "installable": True,
    "application": False,
}
