# Poliedro - Ejemplos de Hotel (DEMO)

Addon para bases de desarrollo. Crea datos ficticios con el prefijo `DEMO |`;
no representa el inventario, huéspedes ni tarifas reales del hotel y no crea
facturas ni pagos.

Al instalarlo en `odoo_dev` quedan estos ejemplos:

- Pisos DEMO 1 y 2.
- Habitaciones 101 (sencilla, 1 persona, $130.000 COP), 102 (doble, 2 personas,
  $185.000 COP) y 201 (compartida, 4 personas, $260.000 COP).
- Comodidades ficticias de Wi-Fi, baño privado y televisor, más un servicio
  ficticio de desayuno por $25.000 COP.
- Huésped DEMO y tres reservas: borrador, confirmada y con check-in; la 102 queda
  reservada y la 201 ocupada para mostrar estados distintos.
- Equipo de aseo y una solicitud de limpieza de ejemplo.

Para recorrerlo, abra Hotel y revise Pisos, Comodidades, Habitaciones, Reservas,
Servicios y Solicitudes de limpieza. Las habitaciones aparecen como productos:
abra una y encontrará su capacidad, tipo, piso, tarifa y comodidades. La tarifa
se expresa en COP como ejemplo, sin impuestos configurados.

Los registros llevan identificadores externos del addon para evitar duplicados
si se reinstala. Al desinstalar el addon DEMO, Odoo elimina esos registros; no
desinstale el módulo proveedor `hotel_management_odoo` para limpiar ejemplos.
