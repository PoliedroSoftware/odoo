{
    "name": "Poliedro POS IoT Health",
    "summary": "Estado, diagnostico y recuperacion de los perifericos IoT del POS",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": [
        "poliedro_pos_iot_proxy",
        "poliedro_pos_scanner_layout",
        "poliedro_pos_authorization_control",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_iot_health/static/src/js/iot_health.js",
            "poliedro_pos_iot_health/static/src/xml/iot_health.xml",
            "poliedro_pos_iot_health/static/src/scss/iot_health.scss",
        ],
    },
    "installable": True,
    "application": False,
}
