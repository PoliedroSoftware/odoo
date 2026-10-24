# Poliedro Payroll Report

Versión 19.0.1.2.1. Desprendible nativo de Odoo 19 Enterprise en A4 horizontal.
Modifica exclusivamente la presentación mediante herencia en `custom-addons`.
Requiere `hr_payroll`; no incorpora código Enterprise ni de proveedores.

## Actualización del addon existente

Se conserva `hr_payroll.action_report_payslip`, su modelo `hr.payslip`, el nombre
`hr_payroll.report_payslip_lang` y el recorrido nativo `/print/payslips`.
No se añade otra acción de impresión. Se mantienen los XML IDs históricos
`report_payslip_poliedro_inherit`, `paperformat_poliedro_payslip_landscape`,
`res_company_form_poliedro_payroll_report` y `payroll_address`.

Antes de editar se compararon los 13 archivos originales con el ZIP del kit:
eran idénticos. La actualización se aplica con `-u poliedro_payroll_report`,
sin desinstalar ni recalcular nóminas. Respaldar base, filestore y addon antes.

```powershell
.venv\Scripts\python.exe -B odoo-bin -c odoo.conf -d odoo_dev -u poliedro_payroll_report --stop-after-init --no-http --max-cron-threads=0
```

Reiniciar el proceso local después de actualizar, manteniendo su configuración.
La publicación en otros ambientes requiere la validación local y la autorización
correspondiente. Este cambio no necesita activar integraciones ni cron.

## Presentación y configuración por compañía

La cabecera integra logo, nombre, NIT, empleado, identificación, período y fechas
como texto seleccionable. El fondo se carga en el nuevo campo administrativo
`poliedro_payroll_header_background`; no debe contener nombres o datos variables.
El fondo del kit se configura como dato de compañía y no se distribuye dentro
del código. Sin fondo se usa el color corporativo; sin logo se conserva el texto.

Se conservan los valores y la semántica de `poliedro_payroll_report_color`,
`poliedro_payroll_tagline`, `poliedro_payroll_footer_phrase` y el banner antiguo.
`poliedro_payroll_banner` permanece almacenado por compatibilidad y no se
reinterpreta como fondo: el diseño integrado usa el nuevo campo. El color de
respaldo sigue siendo `#155E63`; `#073D2E` se configura solo en la compañía elegida.
Cada recibo utiliza su propia compañía, no la compañía activa de la sesión.

El papel es A4 horizontal, márgenes laterales 8.5 mm, superior 7.8 mm e inferior
8 mm, DPI 90. No es el papel predeterminado global. `disable_shrinking` evita que
Qt reduzca las medidas físicas; Odoo ajusta internamente a 96 DPI en Windows.
Una herencia exclusiva de `hr_payroll.report_payslip_lang` fija el DPI efectivo
a 96 también en Linux mediante `data_report_dpi`. Conserva el registro de papel
en 90 DPI y evita el zoom 96/90 que ampliaba el contenido en Linux y enviaba el
pie a una segunda página. No modifica layouts globales ni otros informes.
Las dimensiones usan flujo normal y tablas compatibles con wkhtmltopdf.
Los encabezados de detalle se repiten en las continuaciones; cada recibo del lote
comienza en otra página. El pie es breve y aparece al terminar cada recibo.

## Datos y notas

Se conserva la clasificación original de líneas, los subtotales excluidos,
los aportes patronales excluidos, `earning.total`, `-deduction.total`, la moneda,
las cantidades y `net_wage`. Una devolución reduce las deducciones y mantiene su
signo. El informe nunca llama a `compute_sheet`, contabiliza, paga ni emite a DIAN.
La advertencia sigue dependiendo de `_is_invalid()`.

`printed_at` conserva fecha, hora y zona; `printed_at_display` procede del mismo
instante localizado para mostrar la fecha compacta en la cabecera.

Las descripciones extensas conservan las continuaciones del addon original.
Las notas HTML breves mantienen su formato. Las notas extensas se convierten a
texto legible escapado y se reparten en filas de hasta 250 caracteres, sin
repetir notas ni importes, para evitar que una celda mayor que una página se
superponga al encabezado repetido. Se conserva el contenido textual; el formato
HTML de esas notas extensas no se reproduce. Las tarjetas reducen tipografía
para importes grandes; no se cambia el valor mostrado.

## Tipografía local

Se distribuyen archivos Lato sin modificar obtenidos de
[Google Fonts](https://github.com/google/fonts/tree/main/ofl/lato), con su
licencia SIL OFL en `static/src/fonts/lato/OFL.txt` y procedencia/hashes en
`SOURCE.json`. Se sirven desde el addon, sin CDN durante la impresión.
Se usan Regular, Bold, ExtraBold 800 e Italic. ExtraBold 800 sustituye a Heavy
de la referencia: es una diferencia tipográfica documentada, no una fuente
extraída del PDF. No hace falta instalar fuentes en el sistema operativo.

## Verificación

```powershell
.venv\Scripts\python.exe -B odoo-bin -c odoo.conf -d <base_local_aislada> -u poliedro_payroll_report --test-enable --test-tags /poliedro_payroll_report --stop-after-init --http-interface=127.0.0.1 --http-port=8076 --max-cron-threads=0
```

Los tests cubren clasificación, signos, estados, cantidades, moneda, permisos,
compañías, XML IDs, fondos opcionales, zona horaria, notas largas e impresión
HTTP nativa. La prueba HTTP necesita un recibo ya calculado en la base de pruebas;
un salto de esa prueba no demuestra la impresión. Los datos ficticios de unidad
viven en memoria y no crean liquidaciones reales.

La evidencia privada de esta iteración, los PDFs reales y la comparación visual
se guardan fuera del addon. No publicar muestras con nombres, documentos o
salarios de empleados, respaldos, bases de datos ni configuraciones de acceso.
