/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";

export class SupervisorAuthorizationDialog extends Component {
    static template = "poliedro_pos_authorization_control.SupervisorAuthorizationDialog";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        operationLabel: { type: String, optional: true },
        requireReason: { type: Boolean, optional: true },
        getPayload: Function,
        close: Function,
    };

    setup() {
        this.pos = usePos();
        this.notification = useService("notification");
        this.state = useState({ pin: "", reason: "", checking: false });
    }

    async confirm() {
        if (this.state.pin.length < 4 || (this.props.requireReason && !this.state.reason.trim())) {
            this.notification.add(_t("Digite el PIN y el motivo de la operación."), { type: "warning" });
            return;
        }
        this.state.checking = true;
        try {
            const result = await this.pos.data.call("poliedro.pos.supervisor", "verify_pin", [
                this.state.pin,
                this.pos.config.id,
            ]);
            if (!result?.authorized) {
                this.state.pin = "";
                this.notification.add(_t("PIN de supervisor incorrecto."), { type: "danger" });
                return;
            }
            this.props.getPayload({ ...result, reason: this.state.reason.trim() });
            this.props.close();
        } finally {
            this.state.checking = false;
        }
    }

    cancel() {
        this.props.close();
    }
}

export async function requestPosAuthorization(component, options = {}) {
    const pos = component.pos || component;
    const config = pos.config;
    if (!config.poliedro_authorization_enabled) {
        return { authorized: true, reason: options.reason || "" };
    }
    return await makeAwaitable(component.dialog, SupervisorAuthorizationDialog, {
        title: options.title || _t("Autorización requerida"),
        operationLabel: options.operationLabel || "",
        requireReason: options.requireReason !== false,
    });
}

export async function logPosOperation(component, action, values = {}, authorization = {}) {
    const pos = component.pos || component;
    const order = pos.getOrder?.();
    const product = values.product || order?.getSelectedOrderline?.()?.product_id;
    const payload = {
        action,
        config_id: pos.config?.id,
        session_id: pos.session?.id,
        order_id: order?.id > 0 ? order.id : false,
        order_reference: order?.pos_reference || order?.name || order?.uuid,
        product_id: product?.id,
        cashier_name: pos.getCashier?.()?.name || pos.user?.name,
        supervisor_id: authorization.supervisor_id,
        supervisor_name: authorization.supervisor_name,
        reason: authorization.reason || values.reason || "",
        previous_value: values.previousValue,
        new_value: values.newValue,
        amount: values.amount || 0,
    };
    try {
        await pos.data.call("poliedro.pos.operation.audit", "log_pos_action", [payload]);
    } catch (error) {
        console.warn("Poliedro POS audit could not be stored", error);
    }
}
