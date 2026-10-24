{
    "name": "Poliedro Payroll Report",
    "summary": "Mejora visual del desprendible nativo de nómina de Odoo",
    "version": "19.0.1.2.2",
    "category": "Human Resources/Payroll",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["hr_payroll"],
    "data": [
        "views/res_company_views.xml",
        "report/payslip_report.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "poliedro_payroll_report/static/src/scss/payslip_report.scss",
        ],
    },
    "installable": True,
    "application": False,
}
