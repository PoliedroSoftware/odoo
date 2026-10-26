# Redondeo colombiano de facturas de venta

El addon `poliedro_co_invoice_rounding` usa el redondeo nativo de Odoo 19: una
línea contable explícita sin impuestos que ajusta el total del documento. Solo
se aplica a facturas y notas crédito nuevas en COP de las compañías que tengan
activada la opción en la ficha de empresa.

Las líneas de producto y sus cantidades conservan el cálculo original de Odoo.
No se redondea cada subtotal individual. El motor calcula las líneas e impuestos
sin alterarlos; después redondea una sola vez el total del documento y conserva
la diferencia en la línea nativa de ajuste. El subtotal general incluye esa
línea separada; `price_subtotal` y `price_total` de cada producto permanecen
inalterados.

## Configuración

1. En Contabilidad, habilitar la función nativa **Redondeo de efectivo** si el
grupo contable todavía no la tiene visible.
2. Crear una regla en Contabilidad → Configuración → Redondeo de efectivo con:
   - Precisión: `1.00`
   - Método: `HALF-UP` / `Nearest`
   - Estrategia: agregar línea de ajuste contable
   - Cuentas de ganancias y pérdidas aprobadas por la contadora
3. Abrir la empresa Holding La Labranza S.A.S. y seleccionar la regla en la
   página **Colombian Invoice Rounding**. Activar el redondeo únicamente después
   de que la contadora apruebe ambas cuentas.

La validación impide activar la función si la empresa no usa COP/Colombia, la
regla no es `1.00`/`HALF-UP`/línea contable o faltan cuentas de resultado. No se
modifican facturas publicadas al activar o desactivar la opción.

## Facturación electrónica DIAN

El exportador UBL DIAN mantiene las líneas y bases fiscales calculadas por el
motor. `PayableRoundingAmount` informa la diferencia de la línea de redondeo y
`PayableAmount` suma dicha diferencia al valor previo al redondeo. El addon no
envía facturas a DIAN; la generación de XML en pruebas es local y no transmite
documentos.

## Instalación

```powershell
.venv\Scripts\python.exe odoo-bin -c odoo.conf -d odoo_dev -i poliedro_co_invoice_rounding --stop-after-init --no-http
.venv\Scripts\python.exe odoo-bin -c odoo.conf -d odoo_dev -u poliedro_co_invoice_rounding --stop-after-init --no-http
```

Para una actualización posterior se usa `-u` en la base destino después de
desplegar el addon. Producción y QA requieren respaldo previo, despliegue del
código y lectura de vuelta de módulo/configuración.
