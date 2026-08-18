# Poliedro POS Electronic Invoice Webhook

Este módulo permite seleccionar una o varias órdenes desde **Punto de venta >
Órdenes** y enviarlas a una cola externa de facturación electrónica.

## Configuración

En **Punto de venta > Configuración > Ajustes > Cola de facturación
electrónica** se configuran:

- URL HTTP/HTTPS del webhook.
- Token Bearer opcional.
- Secreto HMAC-SHA256 opcional.
- Tiempo máximo de espera, entre 1 y 60 segundos.

## Uso

1. Marcar las órdenes con los checks de la primera columna.
2. Pulsar **Enviar a facturación electrónica**.
3. Revisar la columna **Cola FE**:
   - `Pendiente`: todavía no se ha enviado.
   - `Enviado a cola`: el webhook respondió con HTTP 2xx.
   - `Error`: el webhook no aceptó la orden o no estuvo disponible.

Las órdenes en error pueden seleccionarse y reenviarse. Las órdenes ya
aceptadas se omiten para evitar duplicados.

## Contrato del webhook

Se envía un `POST` JSON con el evento `pos.order.einvoice.requested`, datos de
empresa, orden, cliente, productos, impuestos y pagos.

Cada orden conserva un `request_id` estable y lo envía también en el encabezado
`Idempotency-Key`. Si se configura un secreto, el cuerpo se firma en
`X-Poliedro-Signature` como `sha256=<firma>`.

El estado `Enviado a cola` confirma únicamente que el webhook respondió con un
código HTTP 2xx. La cola externa debe conservar su propio estado fiscal y
procesar el envío final a la API de facturación electrónica.
