{
    "name": "Poliedro POS - Arqueo térmico 80 mm",
    "summary": "Imprime el arqueo de caja del POS en la impresora térmica IoT",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "website": "https://poliedrosoftware.com",
    "license": "LGPL-3",
    "depends": [
        "point_of_sale",
        "poliedro_pos_iot_proxy",
        "poliedro_pos_receipt",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_cash_closing_receipt/static/src/js/closing_receipt.js",
            "poliedro_pos_cash_closing_receipt/static/src/xml/closing_receipt.xml",
            "poliedro_pos_cash_closing_receipt/static/src/scss/closing_receipt.scss",
        ],
    },
    "installable": True,
    "application": False,
}
