{
    "name": "Poliedro POS Operation Audit",
    "summary": "Trazabilidad de operaciones sensibles realizadas en el punto de venta",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Poliedro Software",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "security/operation_audit_security.xml",
        "views/pos_operation_audit_views.xml",
    ],
    "installable": True,
    "application": False,
}
