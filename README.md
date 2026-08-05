# Custom addons de Poliedro

Este es el único lugar del checkout donde se agrega código propio. Cada
funcionalidad debe ser un addon independiente dentro de esta carpeta y debe
extender Odoo u OCA mediante los mecanismos oficiales de herencia, registries,
assets y vistas heredadas.

No copiar archivos del core para editarlos. Mantener cada addon autocontenido,
con manifiesto, dependencias, seguridad, datos, vistas, frontend y pruebas
declarados explícitamente.

El `addons_path` de desarrollo debe incluir esta carpeta después de `addons` y
`oca-custom`, por ejemplo:

```ini
addons_path = /ruta/al/odoo/addons,/ruta/al/odoo/oca-custom,/ruta/al/odoo/custom-addons
```
