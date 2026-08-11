# Addons personalizados de Poliedro Software

Este repositorio contiene exclusivamente módulos desarrollados por Poliedro
Software para extender Odoo mediante herencia y extensión.

## Reglas

- Crear un módulo instalable independiente por funcionalidad.
- No copiar ni modificar código original de Odoo Community, Odoo Enterprise,
  OCA, Marketplace o proveedores.
- Declarar las dependencias externas en `__manifest__.py`.
- Mantener aquí únicamente código que Poliedro pueda publicar en su repositorio.
- Probar cada cambio en una base de datos de desarrollo antes de desplegarlo.

Las demás fuentes se mantienen separadas en el nivel superior:

- `../oca-addons`: módulos oficiales de OCA.
- `../marketplace-addons`: módulos descargados o comprados en Odoo Apps.
- `../vendor-addons`: código de proveedores específicos.
- `../enterprise`: código oficial de Odoo Enterprise con licencia válida.
