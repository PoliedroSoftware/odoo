"""Create reversible, clearly labelled local hotel examples."""

import base64
from datetime import datetime, time, timedelta
from pathlib import Path

from odoo.fields import Date
from odoo.modules.module import get_module_path


_MODULE = "poliedro_hotel_demo"


def _record(env, model_name, xmlid_name, values):
    imd = env["ir.model.data"].search(
        [("module", "=", _MODULE), ("name", "=", xmlid_name)], limit=1
    )
    if imd:
        return env[model_name].browse(imd.res_id).exists()
    record = env[model_name].create(values)
    env["ir.model.data"].create(
        {
            "module": _MODULE,
            "name": xmlid_name,
            "model": model_name,
            "res_id": record.id,
            "noupdate": True,
        }
    )
    return record


def post_init_hook(env):
    """Seed a small demo property without touching real hotel records."""
    lang = env["res.lang"]._lang_get("es_CO")
    if lang and env.ref("base.user_admin", raise_if_not_found=False):
        admin = env.ref("base.user_admin")
        if admin.partner_id.lang != "es_CO":
            admin.partner_id.lang = "es_CO"

    icon_path = Path(get_module_path("hotel_management_odoo")) / "static" / "description" / "icon.png"
    icon = base64.b64encode(icon_path.read_bytes()).decode("ascii")
    manager = env.ref("base.user_admin", raise_if_not_found=False) or env.user
    company = env.company

    floor_one = _record(
        env,
        "hotel.floor",
        "demo_floor_1",
        {"name": "DEMO | Piso 1", "user_id": manager.id},
    )
    floor_two = _record(
        env,
        "hotel.floor",
        "demo_floor_2",
        {"name": "DEMO | Piso 2", "user_id": manager.id},
    )

    amenities = {}
    for key, name, description in (
        ("wifi", "DEMO | Wi-Fi", "Comodidad ficticia para mostrar la configuración."),
        ("bath", "DEMO | Baño privado", "Comodidad ficticia para mostrar la configuración."),
        ("tv", "DEMO | Televisor", "Comodidad ficticia para mostrar la configuración."),
    ):
        amenities[key] = _record(
            env,
            "hotel.amenity",
            f"demo_amenity_{key}",
            {"name": name, "description": description, "icon": icon},
        )

    rooms = {}
    for key, name, floor, room_type, capacity, price, amenity_keys in (
        ("101", "DEMO | Habitación 101 - Sencilla", floor_one, "single", 1, 130000, ("wifi", "bath")),
        ("102", "DEMO | Habitación 102 - Doble", floor_one, "double", 2, 185000, ("wifi", "bath", "tv")),
        ("201", "DEMO | Habitación 201 - Compartida", floor_two, "dormitory", 4, 260000, ("wifi", "bath")),
    ):
        rooms[key] = _record(
            env,
            "product.template",
            f"demo_room_{key}",
            {
                "name": name,
                "company_id": company.id,
                "type": "consu",
                "is_storable": False,
                "sale_ok": True,
                "purchase_ok": False,
                "taxes_id": [(5, 0, 0)],
                "is_room": True,
                "is_room_avail": True,
                "status": "available",
                "room_type": room_type,
                "num_person": capacity,
                "floor_id": floor.id,
                "list_price": price,
                "room_amenities_ids": [(6, 0, [amenities[item].id for item in amenity_keys])],
            },
        )

    _record(
        env,
        "hotel.service",
        "demo_service_breakfast",
        {"name": "DEMO | Desayuno de muestra", "unit_price": 25000, "taxes_ids": [(5, 0, 0)]},
    )

    guest = _record(
        env,
        "res.partner",
        "demo_guest",
        {"name": "DEMO | Huésped de ejemplo", "company_type": "person", "lang": "es_CO"},
    )
    pricelist = env["product.pricelist"].search(
        [
            ("company_id", "in", [company.id, False]),
            ("currency_id", "=", company.currency_id.id),
        ],
        limit=1,
    )
    if not pricelist:
        raise ValueError("No hay una tarifa de venta en la moneda de la compañía para los ejemplos DEMO.")

    today = Date.context_today(env.user)
    day = env.ref("uom.product_uom_day")
    scenarios = (
        ("draft", "demo_booking_draft", "DEMO | Reserva en borrador", "101", 3, 4),
        ("reserved", "demo_booking_reserved", "DEMO | Reserva confirmada", "102", 5, 6),
        ("checkin", "demo_booking_checkin", "DEMO | Huésped alojado", "201", 0, 1),
    )
    for scenario, xmlid, label, room_key, start_offset, end_offset in scenarios:
        existing = env["ir.model.data"].search(
            [("module", "=", _MODULE), ("name", "=", xmlid)], limit=1
        )
        if existing:
            continue
        start_day = today + timedelta(days=start_offset)
        end_day = today + timedelta(days=end_offset)
        checkin = datetime.combine(start_day, time(15, 0))
        checkout = datetime.combine(end_day, time(11, 0))
        booking = _record(
            env,
            "room.booking",
            xmlid,
            {
                "company_id": company.id,
                "partner_id": guest.id,
                "user_id": guest.id,
                "pricelist_id": pricelist.id,
                "date_order": datetime.combine(today, time(9, 0)),
                "checkin_date": checkin,
                "checkout_date": checkout,
                "hotel_policy": "manual",
            },
        )
        env["room.booking.line"].create(
            {
                "booking_id": booking.id,
                "checkin_date": checkin,
                "checkout_date": checkout,
                "room_id": rooms[room_key].id,
                "uom_id": day.id,
                "uom_qty": 1,
                "price_unit": rooms[room_key].list_price,
                "company_id": company.id,
            }
        )
        booking.message_post(body=label)
        if scenario in ("reserved", "checkin"):
            booking.action_reserve()
        if scenario == "checkin":
            booking.action_checkin()
        if scenario == "draft":
            booking.write({"state": "draft"})
            rooms[room_key].write({"status": "available", "is_room_avail": True})

    team = _record(
        env,
        "cleaning.team",
        "demo_cleaning_team",
        {"name": "DEMO | Equipo de aseo", "team_head_id": manager.id, "member_ids": [(6, 0, [manager.id])]},
    )
    _record(
        env,
        "cleaning.request",
        "demo_cleaning_request",
        {
            "cleaning_type": "room",
            "room_id": rooms["102"].id,
            "team_id": team.id,
            "description": "DEMO | Ejemplo de solicitud de aseo; no corresponde a una tarea real.",
        },
    )
