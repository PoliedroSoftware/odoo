/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { formatCurrency } from "@web/core/currency";
import { _t } from "@web/core/l10n/translation";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { patch } from "@web/core/utils/patch";
import { useEffect, useRef, useState } from "@odoo/owl";


const scannerCurrency = (amount, currencyId) =>
    formatCurrency(amount || 0, currencyId, { digits: [1, 0], minDigits: 0 });

ProductScreen.components = {
    ...ProductScreen.components,
    PaymentScreen,
};


patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.poliedroScannerTable = useRef("poliedroScannerTable");
        this.poliedroScannerState = useState({
            active: this.pos.config.poliedro_scanner_layout_default !== false,
            showNumpad: false,
            payment: false,
        });

        useEffect(
            () => {
                if (!this.poliedroScannerState.active) {
                    return;
                }
                window.requestAnimationFrame(() => {
                    const container = this.poliedroScannerTable.el;
                    const selectedRow = container?.querySelector(".poliedro-scanner-row.is-selected");
                    selectedRow?.scrollIntoView({ block: "nearest", behavior: "smooth" });
                });
            },
            () => [
                this.poliedroScannerState.active,
                this.currentOrder?.uiState?.selected_orderline_uuid,
                this.currentOrder?.lines?.length,
            ]
        );
    },

    get isPoliedroScannerLayout() {
        return Boolean(
            this.poliedroScannerState?.active && !this.pos.isSmallProductScreen
        );
    },

    get poliedroScannerSelectedLine() {
        return this.currentOrder?.getSelectedOrderline();
    },

    get isPoliedroScannerPayment() {
        return Boolean(this.poliedroScannerState?.payment);
    },

    get poliedroScannerItems() {
        return this.currentOrder?.totalQuantity || 0;
    },

    get poliedroScannerLineCount() {
        return this.currentOrder?.lines?.filter((line) => !line.combo_parent_id).length || 0;
    },

    get poliedroScannerSubtotal() {
        return this._poliedroScannerCurrency(this.currentOrder?.priceExcl);
    },

    get poliedroScannerTaxes() {
        return this._poliedroScannerCurrency(this.currentOrder?.amountTaxes);
    },

    get poliedroScannerDiscounts() {
        return this._poliedroScannerCurrency(this.currentOrder?.getTotalDiscount());
    },

    get poliedroScannerTotal() {
        return this._poliedroScannerCurrency(this.currentOrder?.priceIncl);
    },

    get poliedroScannerCustomer() {
        return this.currentOrder?.getPartner();
    },

    get poliedroScannerCreditInfo() {
        const partner = this.poliedroScannerCustomer;
        if (!partner || !partner.pos_credit_limit_enabled) {
            return false;
        }
        return {
            credit_limit: partner.pos_credit_limit_amount || 0,
            used_credit: partner.pos_credit_used_amount || 0,
            available_credit: partner.pos_credit_available_amount || 0,
        };
    },

    togglePoliedroScannerInvoice() {
        if (this.currentOrder?.isToInvoice && this.currentOrder?.setToInvoice) {
            this.currentOrder.setToInvoice(!this.currentOrder.isToInvoice());
        }
    },

    _poliedroScannerCurrency(amount) {
        const currencyId = this.currentOrder?.currency?.id || this.pos.currency.id;
        return scannerCurrency(amount, currencyId);
    },

    togglePoliedroScannerLayout() {
        this.poliedroScannerState.active = !this.poliedroScannerState.active;
        this.poliedroScannerState.showNumpad = false;
        this.poliedroScannerState.payment = false;
        this.numberBuffer.reset();
    },

    async openPoliedroScannerPayment() {
        const order = this.currentOrder;
        if (!order.canPay()) {
            return;
        }

        const missingTrackedLots = order.lines.some(
            (line) => line.getProduct().tracking !== "none" && !line.hasValidProductLot()
        );
        if (
            missingTrackedLots &&
            (this.pos.pickingType.use_create_lots || this.pos.pickingType.use_existing_lots)
        ) {
            const confirmed = await ask(this.env.services.dialog, {
                title: _t("Some Serial/Lot Numbers are missing"),
                body: _t(
                    "You are trying to sell products with serial/lot numbers, but some are missing. Would you like to proceed anyway?"
                ),
            });
            if (!confirmed) {
                return;
            }
        }

        this.numberBuffer.reset();
        this.poliedroScannerState.showNumpad = false;
        this.poliedroScannerState.payment = true;
    },

    closePoliedroScannerPayment() {
        this.poliedroScannerState.payment = false;
        this.numberBuffer.reset();
    },

    togglePoliedroScannerNumpad() {
        if (!this.poliedroScannerSelectedLine) {
            return;
        }
        this.poliedroScannerState.showNumpad = !this.poliedroScannerState.showNumpad;
        this.numberBuffer.reset();
    },

    selectPoliedroScannerQtyLine(event, line) {
        // Clicking the quantity input selects the line without toggling it off.
        event.stopPropagation();
        if (line.combo_parent_id) {
            line = line.combo_parent_id;
        }
        this.pos.selectOrderLine(this.currentOrder, line);
    },

    onPoliedroScannerQtyKeydown(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            event.target.blur();
        }
    },

    updatePoliedroScannerLineQty(event, line) {
        event.stopPropagation();
        if (line.combo_parent_id) {
            line = line.combo_parent_id;
        }
        this.pos.selectOrderLine(this.currentOrder, line);

        const rawValue = event.target.value;
        const newQuantity = parseFloat(rawValue);

        if (!rawValue || Number.isNaN(newQuantity)) {
            event.target.value = line.getQuantity();
            return;
        }

        this.numberBuffer.reset();
        if (newQuantity <= 0) {
            this.currentOrder.removeOrderline(line);
            this.poliedroScannerState.showNumpad = false;
            return;
        }

        // setQuantity recomputes unit price (pricelist), taxes and totals.
        const result = line.setQuantity(newQuantity, Boolean(line.combo_line_ids?.length));
        if (result !== true) {
            this.dialog.add(AlertDialog, result);
            event.target.value = line.getQuantity();
        }
    },

    selectPoliedroScannerLine(event, line) {
        event.stopPropagation();
        this.numberBuffer.reset();
        if (line.isSelected()) {
            this.currentOrder.uiState.selected_orderline_uuid = undefined;
            this.poliedroScannerState.showNumpad = false;
        } else {
            this.pos.selectOrderLine(this.currentOrder, line);
        }
    },

    removePoliedroScannerLineFromRow(event, line) {
        event.stopPropagation();
        if (line.combo_parent_id) {
            line = line.combo_parent_id;
        }
        this.numberBuffer.reset();
        this.currentOrder.removeOrderline(line);
        this.poliedroScannerState.showNumpad = false;
    },

    removePoliedroScannerLine() {
        if (!this.poliedroScannerSelectedLine) {
            return;
        }
        let line = this.poliedroScannerSelectedLine;
        if (line.combo_parent_id) {
            line = line.combo_parent_id;
        }
        this.numberBuffer.reset();
        this.currentOrder.removeOrderline(line);
        this.poliedroScannerState.showNumpad = false;
    },
});
