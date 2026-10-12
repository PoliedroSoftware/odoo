/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const isoDate = (date) => {
    const pad = (value) => String(value).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};

export class PoliedroPosManagementDashboard extends Component {
    static template = "poliedro_pos_management_dashboard.Dashboard";

    setup() {
        this.orm = useService("orm");
        const today = new Date();
        const start = new Date(today);
        start.setDate(today.getDate() - 29);
        this.state = useState({
            dateFrom: isoDate(start), dateTo: isoDate(today), configId: "",
            loading: true, data: null,
        });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        try {
            this.state.data = await this.orm.call(
                "poliedro.pos.management.dashboard", "get_dashboard_data",
                [this.state.dateFrom, this.state.dateTo, this.state.configId || false]
            );
        } finally {
            this.state.loading = false;
        }
    }

    setPreset(days) {
        const end = new Date();
        const start = new Date(end);
        start.setDate(end.getDate() - days + 1);
        this.state.dateFrom = isoDate(start);
        this.state.dateTo = isoDate(end);
        this.load();
    }

    money(value) {
        const currency = this.state.data?.currency || { symbol: "$", position: "before", digits: 0 };
        const number = new Intl.NumberFormat("es-CO", { maximumFractionDigits: currency.digits }).format(value || 0);
        return currency.position === "after" ? `${number} ${currency.symbol}` : `${currency.symbol} ${number}`;
    }

    barWidth(value, rows) {
        const max = Math.max(...(rows || []).map((row) => Math.abs(row.sales || 0)), 1);
        return `width: ${Math.max(3, Math.abs(value || 0) / max * 100)}%`;
    }
}

registry.category("actions").add("poliedro_pos_management_dashboard", PoliedroPosManagementDashboard);
