{
    'name': 'Poliedro Colombia Invoice Rounding',
    'summary': 'Company-specific peso rounding for Colombian sales invoices',
    'author': 'Poliedro Software',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'license': 'LGPL-3',
    'description': 'Company-specific HALF-UP cash rounding for COP invoices with a separate accounting adjustment and DIAN UBL payable rounding amount.',
    'depends': [
        'account',
        'l10n_co_dian',
    ],
    'data': [
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': False,
}

