{
    "name": "Poliedro Invoice Report",
    "summary": "Presentación profesional para el reporte nativo de facturas",
    "version": "19.0.1.10.1",
    "category": "Accounting/Accounting",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["account", "l10n_co_dian", "web"],
    "data": ["report/invoice_report_templates.xml", "report/invoice_report.xml", "report/invoice_report_margin.xml", "report/external_layout_inherit.xml", "views/company_views.xml"],
    "assets": {
        "web.report_assets_common": [
            "poliedro_invoice_report/static/src/scss/invoice_report.scss",
        ],
    },
    "installable": True,
    "application": False,
}
