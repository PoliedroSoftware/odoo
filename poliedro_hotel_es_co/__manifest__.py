{
    "name": "Poliedro - Hotel en Español Colombia",
    "version": "19.0.1.0.0",
    "category": "Services/Hotel",
    "summary": "Traducción colombiana del módulo Hotel Management de Cybrosys",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["hotel_management_odoo"],
    "assets": {
        "web.assets_backend": [
            "poliedro_hotel_es_co/static/src/js/hotel_terms.js",
        ],
    },
    "post_load": "post_load_hook",
    "installable": True,
    "application": False,
}
