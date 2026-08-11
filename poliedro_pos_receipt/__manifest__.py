{
    "name": "Poliedro POS Receipt",
    "summary": "Recibo POS personalizado de Poliedro",
    "version": "19.0.1.0.1",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "views/pos_config_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_receipt/static/src/js/pos_orderline.js",
            "poliedro_pos_receipt/static/src/xml/pos_receipt.xml",
            "poliedro_pos_receipt/static/src/xml/pos_orderline.xml",
            "poliedro_pos_receipt/static/src/scss/pos_receipt.scss",
        ],
    },
    "installable": True,
    "application": False,
}
