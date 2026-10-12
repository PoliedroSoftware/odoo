{
    "name": "Poliedro POS Refund by Receipt",
    "summary": "Acceso rápido a devoluciones escaneando el recibo original",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "poliedro_pos_scanner_layout", "poliedro_pos_authorization_control"],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_refund_by_receipt/static/src/js/refund_by_receipt.js",
            "poliedro_pos_refund_by_receipt/static/src/xml/refund_by_receipt.xml",
            "poliedro_pos_refund_by_receipt/static/src/scss/refund_by_receipt.scss",
        ],
    },
    "installable": True,
    "application": False,
}
