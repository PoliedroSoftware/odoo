/** @odoo-module **/

import { Component, onWillDestroy, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class DianBatchProgress extends Component {
    static template = "poliedro_dian_batch_progress.Progress";

    setup() {
        this.orm = useService("orm");
        this.state = useState({ data: null, open: false });
        onWillStart(() => this.refresh());
        this.timer = setInterval(() => this.refresh(), 12000);
        onWillDestroy(() => clearInterval(this.timer));
    }

    async refresh() {
        try {
            this.state.data = await this.orm.call(
                "poliedro.dian.send.batch",
                "get_navbar_progress",
                []
            );
        } catch {
            this.state.data = null;
        }
    }
}

registry.category("systray").add(
    "poliedro_dian_batch_progress",
    { Component: DianBatchProgress, isDisplayed: (env) => {
        const controller = env.services.action.currentController;
        return controller?.props?.resModel === "account.move";
    } },
    { sequence: 200 }
);
