/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { formatCurrency } from "@web/core/currency";
import { patch } from "@web/core/utils/patch";
import { useEffect, useRef, useState } from "@odoo/owl";


const scannerCurrency = (amount, currencyId) =>
    formatCurrency(amount || 0, currencyId, { digits: [1, 0], minDigits: 0 });


patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.poliedroScannerTable = useRef("poliedroScannerTable");
        const storageKey = `poliedro_pos_scanner_layout_${this.pos.config.id}`;
        const storedMode = window.localStorage.getItem(storageKey);
        const defaultMode = Boolean(this.pos.config.poliedro_scanner_layout_default);
        this.poliedroScannerState = useState({
            active: storedMode === null ? defaultMode : storedMode === "scanner",
            showNumpad: false,
            storageKey,
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

    _poliedroScannerCurrency(amount) {
        const currencyId = this.currentOrder?.currency?.id || this.pos.currency.id;
        return scannerCurrency(amount, currencyId);
    },

    togglePoliedroScannerLayout() {
        this.poliedroScannerState.active = !this.poliedroScannerState.active;
        this.poliedroScannerState.showNumpad = false;
        window.localStorage.setItem(
            this.poliedroScannerState.storageKey,
            this.poliedroScannerState.active ? "scanner" : "classic"
        );
        this.numberBuffer.reset();
    },

    togglePoliedroScannerNumpad() {
        if (!this.poliedroScannerSelectedLine) {
            return;
        }
        this.poliedroScannerState.showNumpad = !this.poliedroScannerState.showNumpad;
        this.numberBuffer.reset();
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
