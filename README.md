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

## Suite operativa POS

Los controles operativos desarrollados por Poliedro están separados por
responsabilidad:

- `poliedro_pos_authorization_control`: PIN cifrado de supervisor para
  operaciones sensibles.
- `poliedro_pos_operation_audit`: trazabilidad de descuentos, cambios de
  precio, eliminaciones, anulaciones, devoluciones y aperturas de cajón.
- `poliedro_pos_cash_move_reason`: catálogo obligatorio para entradas y
  salidas de efectivo.
- `poliedro_pos_default_cash_payment`: selecciona efectivo automáticamente al
  abrir el cobro, sin impedir que el cajero cambie el método de pago.
- `poliedro_pos_price_check`: consulta de precio, promoción e inventario sin
  agregar el artículo a la orden.
- `poliedro_pos_refund_by_receipt`: búsqueda rápida de la venta original por
  QR o número de recibo.
- `poliedro_stock_expiration_alert`: alertas de vencimiento y retiro seguro
  mediante el flujo estándar de desecho de inventario.
- `poliedro_pos_management_dashboard`: indicadores gerenciales de venta,
  margen, caja, auditoría y rotación.

Las autorizaciones se entregan desactivadas hasta que exista al menos un
supervisor con PIN. Después de configurar el supervisor, se activan desde la
configuración del punto de venta.
