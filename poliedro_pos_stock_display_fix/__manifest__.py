{
    "name": "Poliedro POS Stock Display Fix",
    "version": "19.0.1.0.0",
    "category": "Sales/Point of Sale",
    "summary": "Compatibility fix for the OCA POS stock display on Odoo 19",
    "author": "Poliedro Software",
    "license": "AGPL-3",
    "depends": ["pos_stock_available_online"],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_stock_display_fix/static/src/app/product_card.js",
        ],
    },
    "installable": True,
    "application": False,
}
