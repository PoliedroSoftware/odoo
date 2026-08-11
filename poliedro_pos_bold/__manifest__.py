{
    "name": "Poliedro POS Bold",
    "summary": "Cobros Bold NEO mediante Applink y codigo QR",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "views/pos_payment_method_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_bold/static/src/js/bold_payment_dialog.js",
            "poliedro_pos_bold/static/src/js/payment_bold.js",
            "poliedro_pos_bold/static/src/xml/bold_payment_dialog.xml",
            "poliedro_pos_bold/static/src/scss/bold_payment_dialog.scss",
        ],
    },
    "installable": True,
    "application": False,
}
