{
    "name": "Poliedro POS Authorization Control",
    "summary": "Autorización mediante PIN para operaciones sensibles del POS",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "poliedro_pos_operation_audit", "poliedro_pos_scanner_layout"],
    "data": [
        "security/ir.model.access.csv",
        "security/supervisor_security.xml",
        "views/pos_supervisor_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "poliedro_pos_authorization_control/static/src/js/authorization_service.js",
            "poliedro_pos_authorization_control/static/src/js/authorization_patches.js",
            "poliedro_pos_authorization_control/static/src/xml/supervisor_authorization_dialog.xml",
            "poliedro_pos_authorization_control/static/src/scss/authorization.scss",
        ],
    },
    "installable": True,
    "application": False,
}
