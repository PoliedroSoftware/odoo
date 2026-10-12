from collections import defaultdict
from datetime import datetime, time

from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class PoliedroPosManagementDashboard(models.AbstractModel):
    _name = "poliedro.pos.management.dashboard"
    _description = "Datos del tablero gerencial del POS"

    @api.model
    def get_dashboard_data(self, date_from, date_to, config_id=False):
        if not self.env.user.has_group("point_of_sale.group_pos_manager"):
            raise AccessError(_("Solo los administradores del punto de venta pueden ver este tablero."))
        start = datetime.combine(fields.Date.to_date(date_from), time.min)
        end = datetime.combine(fields.Date.to_date(date_to), time.max)
        domain = [
            ("date_order", ">=", fields.Datetime.to_string(start)),
            ("date_order", "<=", fields.Datetime.to_string(end)),
            ("state", "in", ["paid", "done", "invoiced"]),
        ]
        if config_id:
            domain.append(("config_id", "=", int(config_id)))
        orders = self.env["pos.order"].search(domain)
        lines = orders.lines
        currency = self.env.company.currency_id

        gross_sales = sum(order.amount_total for order in orders if order.amount_total >= 0)
        refunds = abs(sum(order.amount_total for order in orders if order.amount_total < 0))
        net_sales = sum(orders.mapped("amount_total"))
        margin = sum(orders.mapped("margin"))
        discount_total = sum(
            abs(line.price_unit * line.qty) * (line.discount or 0) / 100 for line in lines
        )

        cashier_data = defaultdict(lambda: {"orders": 0, "sales": 0.0, "refunds": 0.0})
        hourly_data = defaultdict(lambda: {"orders": 0, "sales": 0.0})
        for order in orders:
            cashier = order.user_id.name or _("Sin cajero")
            cashier_data[cashier]["orders"] += 1
            if order.amount_total < 0:
                cashier_data[cashier]["refunds"] += abs(order.amount_total)
            else:
                cashier_data[cashier]["sales"] += order.amount_total
            local_date = fields.Datetime.context_timestamp(self, order.date_order)
            hour_key = f"{local_date.hour:02d}:00"
            hourly_data[hour_key]["orders"] += 1
            hourly_data[hour_key]["sales"] += order.amount_total

        product_data = defaultdict(lambda: {"qty": 0.0, "sales": 0.0, "margin": 0.0})
        category_data = defaultdict(lambda: {"qty": 0.0, "sales": 0.0})
        for line in lines:
            product_name = line.product_id.display_name
            product_data[product_name]["qty"] += line.qty
            product_data[product_name]["sales"] += line.price_subtotal_incl
            product_data[product_name]["margin"] += line.margin
            categories = line.product_id.pos_categ_ids
            category_name = categories[:1].name if categories else _("Sin categoría")
            category_data[category_name]["qty"] += line.qty
            category_data[category_name]["sales"] += line.price_subtotal_incl

        audit_domain = [("operation_datetime", ">=", start), ("operation_datetime", "<=", end)]
        if config_id:
            audit_domain.append(("config_id", "=", int(config_id)))
        audits = self.env["poliedro.pos.operation.audit"].search(audit_domain)
        audit_counts = {key: 0 for key in ["discount", "price_change", "line_delete", "refund", "order_cancel", "cashbox_open"]}
        for action, count in self.env["poliedro.pos.operation.audit"]._read_group(
            audit_domain, ["action"], ["__count"]
        ):
            audit_counts[action] = count

        session_domain = [
            ("stop_at", ">=", start), ("stop_at", "<=", end),
            ("state", "=", "closed"),
        ]
        if config_id:
            session_domain.append(("config_id", "=", int(config_id)))
        sessions = self.env["pos.session"].search(session_domain)
        cash_difference = sum(sessions.mapped("cash_register_difference"))

        sold_qty_by_product = defaultdict(float)
        for line in lines:
            sold_qty_by_product[line.product_id.id] += line.qty
        stock_products = self.env["product.product"].search([
            ("available_in_pos", "=", True), ("is_storable", "=", True), ("qty_available", ">", 0)
        ])
        low_rotation = sorted(
            [{"name": product.display_name, "stock": product.qty_available,
              "sold": sold_qty_by_product.get(product.id, 0.0)} for product in stock_products
             if sold_qty_by_product.get(product.id, 0.0) <= 1],
            key=lambda item: (-item["stock"], item["name"]),
        )[:10]

        def top_rows(mapping, limit=8, sort_key="sales"):
            return [dict(name=name, **values) for name, values in sorted(
                mapping.items(), key=lambda item: item[1].get(sort_key, 0), reverse=True
            )[:limit]]

        positive_orders = orders.filtered(lambda order: order.amount_total >= 0)
        return {
            "currency": {"symbol": currency.symbol, "position": currency.position, "digits": currency.decimal_places},
            "kpis": {
                "gross_sales": gross_sales, "refunds": refunds, "net_sales": net_sales,
                "margin": margin, "margin_percent": (margin / net_sales * 100) if net_sales else 0,
                "discounts": discount_total, "orders": len(orders),
                "average_ticket": gross_sales / len(positive_orders) if positive_orders else 0,
                "cash_difference": cash_difference,
            },
            "cashiers": top_rows(cashier_data),
            "hours": [dict(name=key, **hourly_data[key]) for key in sorted(hourly_data)],
            "products": top_rows(product_data),
            "categories": top_rows(category_data),
            "low_rotation": low_rotation,
            "audit": audit_counts,
            "audit_total": len(audits),
            "configs": self.env["pos.config"].search_read([], ["name"]),
        }
