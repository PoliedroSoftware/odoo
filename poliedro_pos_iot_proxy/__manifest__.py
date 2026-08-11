{
    "name": "Poliedro POS IoT Proxy",
    "summary": "Puente local confiable para impresora, cajon y bascula del POS",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_iot_proxy/static/src/js/iot_proxy.js",
        ],
    },
    "installable": True,
    "application": False,
}
