# Poliedro Invoice Report

Rediseña la factura PDF de cliente de Colombia mediante QWeb heredado. No añade
modelos contables, acciones de informe ni motores PDF alternativos.

## Inspección técnica de Odoo 19

- La acción de impresión estándar es `account.account_invoices`, un
  `ir.actions.report` para `account.move` con `report_name`=
  `account.report_invoice_with_payments` y tipo `qweb-pdf`.
- La plantilla común es `account.report_invoice_document`; el contenedor de
  impresión con pagos es `account.report_invoice_with_payments`.
- El addon hereda `account.report_invoice_document`, sin reemplazarla. La
  plantilla primaria DIAN `l10n_co_dian.report_invoice_document` hereda a su vez
  la plantilla común, por lo que conserva sus datos técnicos y añade el nuevo
  cuerpo visual en el reporte aceptado. El layout estándar y la acción de
  impresión no cambian.
- El addon no edita los archivos de `addons/` ni `enterprise/`.

## Datos utilizados

Los datos de identificación, líneas e importes provienen de registros estándar:

- Factura: `name`, `invoice_date`, `invoice_date_due`, `partner_id`, `ref`,
  `payment_reference`, `invoice_payment_term_id`, `invoice_line_ids`,
  `amount_untaxed`, `amount_tax`, `amount_total`, `amount_residual`, `state` y
  `payment_state`.
- Empresa: `company_id`, `company_id.partner_id`, `logo`, `vat`, `email`,
  `phone` y dirección del contacto de compañía.
- DIAN Colombia: `l10n_co_dian_attachment_id`,
  `l10n_co_edi_cufe_cude_ref` (referencia calculada) y el método nativo
  `_l10n_co_dian_get_extra_invoice_report_values()`, que obtiene `barcode_src`,
  `signing_datetime` e `identifier` desde el último documento aceptado.
- Resolución y rango: campos del diario
  `l10n_co_edi_dian_authorization_number`,
  `l10n_co_edi_dian_authorization_date`,
  `l10n_co_edi_dian_authorization_end_date`, `l10n_co_edi_min_range_number` y
  `l10n_co_edi_max_range_number`.
- Identidad tributaria: `l10n_co_edi_large_taxpayer`,
  `l10n_co_edi_obligation_type_ids`, `_l10n_co_edi_get_fiscal_regimen_name()` y
  `l10n_co_edi_header_actividad_economica`.

Los valores monetarios no se vuelven a calcular en el reporte. El importe pagado
se muestra como `amount_total - amount_residual`, usando los importes calculados
por Odoo. El estado usa `state` y `payment_state`; el reporte nunca deduce que
un documento está pagado a partir de fechas.

## Diseño y personalización

- Verde oscuro, verde medio, dorado, blanco y grises claros, con tarjetas,
  franja de datos, tabla de líneas, totales, estado y bloques DIAN.
- Emisor y cliente se distribuyen en dos columnas iguales que aprovechan el
  ancho disponible. La franja inferior reparte el espacio entre los datos
  presentes (fechas, método de pago, código de cliente y referencia), mediante
  tablas compatibles con wkhtmltopdf.
- El logo y la información fiscal salen de la compañía del documento.
- Opcionalmente, en **Ajustes → Empresas → Diseño de factura PDF** se pueden
  cargar una imagen panorámica, un mensaje corto, tres mensajes de marca y una
  frase de pie. Los tres mensajes de marca se dibujan con iconos dentro de la
  cabecera; se omiten cuando la empresa no los configura.
- La imagen de cabecera es opcional. La referencia visual incluye una foto de
  estación y frases de marca que no se copian como datos fijos.
- Las notas, secciones, subtotales, descuentos e impuestos permanecen en las
  líneas reales; no se insertan ejemplos ni conceptos fijos.
- El diseño se aplica a facturas de cliente y notas crédito. Facturas de
  proveedor mantienen el reporte nativo. Las secciones de DIAN solo aparecen
  cuando el documento tiene adjunto electrónico aceptado.
- Se conserva el formato A4 y el comportamiento de varias páginas del reporte
  nativo. No se crea `ir.actions.report` nuevo.
- El margen superior se reduce a 12 mm solo al imprimir un lote compuesto
  enteramente por facturas de cliente o notas crédito. Los documentos de
  proveedor y lotes mixtos conservan el margen de la acción nativa.

## Instalación / actualización en una base de desarrollo

Con Enterprise y `l10n_co_dian` disponibles en `addons_path`:

```powershell
.venv\Scripts\python.exe odoo-bin -c odoo.conf -d <base_pruebas> -i poliedro_invoice_report --stop-after-init --no-http --max-cron-threads=0
```

Para cambios posteriores, reemplaza `-i` por `-u`. Antes de instalar o actualizar,
respalda la base y su filestore. La actualización no debe ejecutarse sobre
producción sin una revisión y autorización de despliegue independiente.

## Prueba de PDF

Usa `account.account_invoices` para imprimir desde el botón estándar. Para prueba
automatizada, ejecuta `ir.actions.report._render_qweb_pdf` con una factura
existente de la base de pruebas y confirma que nombre, fechas, cliente, líneas,
totales, estado, CUFE y QR coinciden con el registro y el documento DIAN aceptado.
No uses una prueba de impresión para volver a emitir a DIAN ni enviar el correo.
En QA se verificó el reporte nativo `account.account_invoices` con facturas
aceptadas por DIAN y pagadas, contrastando importes, QR, CUFE, firma, resolución
y rango. También se imprimieron cinco facturas de dos compañías y borradores
con descripciones y direcciones extensas para comprobar la paginación.

La versión `19.0.1.10.1` se validó en `odoo_dev` con el motor nativo wkhtmltopdf:
tarjetas de emisor y cliente al 50 %, franja de cuatro y cinco datos, facturas
de una página y un borrador temporal de 36 líneas en dos páginas con encabezados
repetidos y totales al final. La cabecera, los conceptos, los importes, el bloque
DIAN y el pie conservaron su contenido respecto a la versión anterior.

Los cambios de prueba se revirtieron y se comprobó que no quedaron borradores
temporales. Los PDF de evidencia se conservan localmente y no se publican en
este repositorio, ya que pueden contener datos de compañías y documentos reales.

La base de pruebas no contiene facturas parcialmente pagadas ni en proceso de
pago; esos estados están mapeados en la plantilla, pero no se verificaron contra
un documento real de QA. Tampoco se creó un pago ni se publicó un asiento para
simularlos.

## Extensiones relevantes

- Herencias: `account.report_invoice_document` (estructura visual nativa),
  las siete variantes `web.external_layout_*` (ocultar encabezado/dirección/pie
  nativos solo para facturas de cliente), y los estilos de
  `web.report_assets_common`.
- Contenido reusable: `poliedro_invoice_report.invoice_document_body`.
- Ajuste de margen condicional: `poliedro_invoice_report.report_invoice_poliedro_sale_margin`.
- Acción nativa preservada: `account.account_invoices`.
- El QR y los datos de firma se obtienen mediante el método del módulo DIAN;
  resolución, rango, obligaciones, régimen y actividad salen de los campos de
  diario, contacto y compañía de la localización.
