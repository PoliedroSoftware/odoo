# Acceso SSH temporal desde GitHub Actions

Acción compartida de Poliedro, sin paquetes npm externos. Autoriza únicamente
la IPv4 `/32` del runner actual en TCP 22 mediante la API de DigitalOcean.
El script `post` retira esa misma autorización al finalizar el job, incluso
si falla un paso posterior. Nunca sustituye todas las reglas del firewall.

## Condiciones de uso

- Token dedicado con **solo** `firewall:read` y `firewall:update`, guardado en
  GitHub como secreto `DO_FIREWALL_TOKEN`. No reutilizar el token administrativo
  del equipo ni escribirlo en archivos, logs o repositorios.
- Runner hospedado por GitHub, evento `push` o `workflow_dispatch`, rama `main`.
- Repositorio expresamente autorizado en `access.cjs`.
- Firewall vinculado exclusivamente al droplet esperado, sin etiquetas que
  amplíen el conjunto de servidores afectados.
- IP del runner pública y perteneciente a los rangos actuales de Actions
  publicados por GitHub. Se determina por HTTPS, no mediante un input arbitrario.
- La clave SSH existente y la validación de host conocido siguen siendo
  obligatorias: abrir una regla no sustituye la autenticación SSH.

La acción conserva las autorizaciones previas, incluida la IP del operador.
Si la `/32` ya existía antes del job, no se considera propiedad de esta acción
y no se elimina. Nunca abre `0.0.0.0/0` ni una subred del proveedor de runners.

## Instalación

1. Crear el token en DigitalOcean → API → Generate New Token → Custom Scopes.
   Escoger únicamente lectura y actualización de firewalls.
2. Guardarlo como `DO_FIREWALL_TOKEN` en los repositorios que desplieguen.
   No pegarlo en el chat. Desde una terminal propia:

   ```powershell
   gh secret set DO_FIREWALL_TOKEN --repo PoliedroSoftware/odoo
   gh secret set DO_FIREWALL_TOKEN --repo PoliedroSoftware/odoo-holdinglalabranza
   ```

   Cada comando solicita el valor de forma interactiva. No usar `--body` con
   el token literal en la línea de comandos ni dejarlo en el historial.

3. Publicar la acción y los cambios de workflow mediante PR, manteniendo las
   protecciones existentes. No desactivar revisiones para integrar el cambio.
4. En el repo transversal se usa la acción local después de checkout.
   En el repo del cliente se debe referenciar esta misma acción con el SHA
   completo del commit revisado de `PoliedroSoftware/odoo`, sin copiarla ni
   depender de una rama mutable. Ese SHA se obtiene después de publicar el PR.
5. Ejecutar una prueba real de conectividad/CI y comprobar después por API
   que la regla temporal desapareció. Los tests locales no prueban ese circuito.
   La pipeline transversal incorpora `connection_test_only=true`: prueba
   firewall, clave SSH y respuesta pública de Odoo, omitiendo la carga de
   módulos y cualquier actualización de esquema o reinicio del servicio.
   Un push que solo cambie la automatización también utiliza ese modo seguro;
   los cambios en addons o en el script de despliegue conservan el despliegue.

No se crean, redimensionan ni eliminan droplets. Ambos endpoints de reglas
(agregar y retirar) utilizan el permiso `firewall:update`.

## Cancelaciones y recuperación

GitHub ejecuta el `post` con `always()`. Sin embargo, perder por completo la
máquina del runner o forzar su terminación puede impedir cualquier cleanup:
DigitalOcean no establece un TTL nativo para esta regla. No se promete una
caducidad independiente del runner.

La dirección `/32` queda identificada en el log de autorización del job. Si
falló el cleanup o murió el runner, el operador debe comprobar y retirar
**solo esa dirección**, conservando la regla de administración:

```text
doctl compute firewall remove-rules <firewall-id> --inbound-rules "protocol:tcp,ports:22,address:<runner-ip>/32"
```

La acción reintenta el cleanup y falla de forma visible si no confirma su
retirada. Después de una prueba real debe verificarse también el acceso del
administrador y la salud de Odoo.

## Pruebas

```text
node --test .github/actions/digitalocean-ssh/test/*.test.cjs
```

Cubren CIDR restringido, contexto de despliegue, permisos previos, IP ajena a
GitHub, firewall compartido, POST ambiguo, fallo de propagación SSH, propiedad
del cleanup e idempotencia. No utilizan credenciales reales ni cambian reglas.

## Referencias

- [Permiso firewall:update](https://docs.digitalocean.com/reference/api/scopes/firewall/update/).
- [Creación de tokens limitados](https://docs.digitalocean.com/reference/api/create-personal-access-token/).
- [Red y direcciones de runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
- [Post-actions y cleanup](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax).
