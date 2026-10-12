#!/usr/bin/env bash
set -Eeuo pipefail
archive="${1:-}"
module_csv="${2:-}"
install_modules="${3:-}"
requested_updates="${4:-}"
[[ "$archive" =~ ^poliedro-[0-9a-f]{40}\.tar\.gz$ ]] || { echo "Paquete inválido." >&2; exit 2; }
valid_list() { [[ -z "$1" || "$1" =~ ^poliedro_[A-Za-z0-9_]+(,poliedro_[A-Za-z0-9_]+)*$ ]]; }
valid_list "$module_csv" && [[ -n "$module_csv" ]] || { echo "Inventario de addons inválido." >&2; exit 2; }
valid_list "$install_modules" && valid_list "$requested_updates" || { echo "Lista de módulos inválida." >&2; exit 2; }
base=/opt/poliedro-odoo
compose=(docker compose -f "$base/compose.yml" -p poliedro-odoo)
addons="$base/src/custom-addons"
incoming="$base/incoming/$archive"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="$base/backups/poliedro-staging/$stamp"
stage="$base/sync/poliedro-$stamp"
[[ -f "$incoming" && -d "$addons" ]] || { echo "No se encontró paquete o destino." >&2; exit 2; }
mkdir -p "$(dirname "$backup")" "$base/sync" "$stage/addons"
mkdir -m 700 "$backup"
mkdir -p "$backup/previous" "$backup/failed"
tar -tzf "$incoming" | while IFS= read -r p; do [[ "$p" != /* && "$p" != *"../"* && "$p" != ".." ]] || exit 2; done
tar -xzf "$incoming" --no-same-owner --no-same-permissions -C "$stage/addons"
[[ -z "$(find "$stage/addons" -type l -print -quit)" ]] || { echo "No se aceptan symlinks." >&2; exit 2; }
modules=()
for d in "$stage/addons"/*; do
  [[ -d "$d" && -f "$d/__manifest__.py" ]] || { echo "Addon inválido." >&2; exit 2; }
  name="$(basename "$d")"
  [[ "$name" =~ ^poliedro_[A-Za-z0-9_]+$ ]] || { echo "Nombre inválido: $name" >&2; exit 2; }
  modules+=("$name")
done
((${#modules[@]} > 0)) || { echo "Paquete vacío." >&2; exit 2; }
IFS=',' read -ra expected <<< "$module_csv"
for name in "${expected[@]}"; do [[ " ${modules[*]} " == *" $name "* ]] || { echo "Falta addon: $name" >&2; exit 2; }; done
[[ "$(printf '%s\n' "${expected[@]}" | sort -u)" == "$(printf '%s\n' "${modules[@]}" | sort -u)" ]] || { echo "El inventario de módulos no coincide." >&2; exit 2; }
for value in "$install_modules" "$requested_updates"; do
  [[ -z "$value" ]] && continue
  IFS=',' read -ra chosen <<< "$value"
  for name in "${chosen[@]}"; do [[ " ${modules[*]} " == *" $name "* ]] || { echo "Addon fuera del paquete: $name" >&2; exit 2; }; done
done

deployment_started=0
db_backup=0
changed=()
rollback() {
  status=$?
  trap - ERR EXIT
  set +e
  if (( deployment_started )); then
    "${compose[@]}" stop odoo
    for name in "${changed[@]}"; do
      target="$addons/$name"
      [[ ! -e "$target" ]] || mv "$target" "$backup/failed/$name"
      [[ ! -e "$backup/previous/$name" ]] || mv "$backup/previous/$name" "$target"
    done
    if (( db_backup )); then
      "${compose[@]}" exec -T db pg_restore --clean --if-exists --no-owner --no-acl -U odoo -d odoo_dev < "$backup/odoo_dev.dump"
      if [[ -f "$backup/filestore.tar.gz" ]]; then
        filestore="$base/data/odoo/filestore"
        if [[ -e "$filestore/odoo_dev" ]]; then mv "$filestore/odoo_dev" "$backup/filestore-failed"; fi
        tar -xzf "$backup/filestore.tar.gz" -C "$filestore"
      fi
    fi
    "${compose[@]}" up -d odoo
  fi
  exit "$status"
}
trap rollback ERR EXIT

cp -a "$base/compose.yml" "$backup/compose.yml"
"${compose[@]}" stop odoo
deployment_started=1
"${compose[@]}" exec -T db pg_dump -U odoo -Fc --no-owner --no-acl odoo_dev > "$backup/odoo_dev.dump"
[[ -s "$backup/odoo_dev.dump" ]] || { echo "Backup vacío." >&2; exit 1; }
db_backup=1
if [[ -d "$base/data/odoo/filestore/odoo_dev" ]]; then
  tar -czf "$backup/filestore.tar.gz" -C "$base/data/odoo/filestore" odoo_dev
fi
installed="$("${compose[@]}" exec -T db psql -U odoo -d odoo_dev -Atc "SELECT name FROM ir_module_module WHERE state='installed' ORDER BY name")"
mapfile -t installed_custom < <(comm -12 <(printf '%s\n' "${modules[@]}" | sort -u) <(printf '%s\n' "$installed" | sort -u))

for name in "${modules[@]}"; do
  changed+=("$name")
  [[ ! -e "$addons/$name" ]] || mv "$addons/$name" "$backup/previous/$name"
  mv "$stage/addons/$name" "$addons/$name"
done
requested=()
[[ -z "$requested_updates" ]] || IFS=',' read -ra requested <<< "$requested_updates"
updates="$(printf '%s\n' "${installed_custom[@]}" "${requested[@]}" | sed '/^$/d' | sort -u | paste -sd, -)"
odoo_args=(-d odoo_dev)
[[ -z "$install_modules" ]] || odoo_args+=(-i "$install_modules")
[[ -z "$updates" ]] || odoo_args+=(-u "$updates")
if ((${#odoo_args[@]} > 1)); then "${compose[@]}" run --rm odoo "${odoo_args[@]}" --stop-after-init; fi
"${compose[@]}" up -d odoo
for attempt in $(seq 1 45); do
  if "${compose[@]}" exec -T odoo python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8069/web/login', timeout=3)" >/dev/null 2>&1; then
    deployment_started=0
    trap - ERR EXIT
    mv "$incoming" "$backup/source-addons.tar.gz"
    echo "Despliegue verificado. Backup: $backup/odoo_dev.dump"
    exit 0
  fi
  sleep 2
done
"${compose[@]}" logs --tail=100 odoo >&2
echo "Odoo no pasó la verificación de salud." >&2
false
