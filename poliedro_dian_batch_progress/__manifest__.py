{
    "name": "Poliedro DIAN Batch Progress",
    "summary": "Seguimiento visual y envío pausado de facturas electrónicas DIAN",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["account", "l10n_co_dian", "web"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "poliedro_dian_batch_progress/static/src/js/dian_batch_progress.js",
            "poliedro_dian_batch_progress/static/src/xml/dian_batch_progress.xml",
            "poliedro_dian_batch_progress/static/src/scss/dian_batch_progress.scss",
        ],
    },
    "installable": True,
    "application": False,
}
