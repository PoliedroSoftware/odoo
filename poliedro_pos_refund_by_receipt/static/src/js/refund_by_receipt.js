/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";

export class ReceiptLookupDialog extends Component {
    static template = "poliedro_pos_refund_by_receipt.ReceiptLookupDialog";
    static components = { Dialog };
    static props = { getPayload: Function, close: Function };
    setup() { this.state = useState({ reference: "" }); }
    confirm() {
        const value = this.state.reference.trim();
        if (!value) return;
        this.props.getPayload(value);
        this.props.close();
    }
    cancel() { this.props.close(); }
}

patch(ProductScreen.prototype, {
    async openPoliedroRefundByReceipt() {
        const reference = await makeAwaitable(this.dialog, ReceiptLookupDialog, {});
        if (!reference) return;

        let stateOverride = {
            filter: "SYNCED",
            search: { fieldName: "RECEIPT_NUMBER", searchTerm: reference },
            destinationOrder: this.currentOrder,
        };
        try {
            const parsed = new URL(reference);
            const uuid = parsed.searchParams.get("order_uuid");
            if (uuid) {
                const orders = await this.pos.data.loadServerOrders([["uuid", "=", uuid]]);
                if (!orders.length) {
                    this.notification.add(_t("No se encontró el recibo escaneado."), { type: "warning" });
                    return;
                }
                stateOverride = {
                    ...stateOverride,
                    selectedOrderUuid: orders[0].uuid,
                    search: { fieldName: "RECEIPT_NUMBER", searchTerm: orders[0].pos_reference || "" },
                };
            }
        } catch {
            // A receipt number is expected to not be a URL.
        }
        this.pos.navigate("TicketScreen", { stateOverride });
    },
});
