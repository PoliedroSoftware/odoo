/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { formatCurrency } from "@web/core/currency";
import { _t } from "@web/core/l10n/translation";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { patch } from "@web/core/utils/patch";
import { useEffect, useExternalListener, useRef, useState } from "@odoo/owl";


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
        this.poliedroScannerLastKeyboardInputAt = 0;
        useExternalListener(
            document,
            "keydown",
            (event) => this.onPoliedroScannerGlobalKeydown(event),
            { capture: true }
        );
        useExternalListener(window, "poliedro-scanner-show-classic", () => {
            if (this.isPoliedroScannerLayout) {
                this.togglePoliedroScannerLayout();
            }
        });
        useExternalListener(window, "poliedro-scanner-close-payment", () => {
            if (this.isPoliedroScannerPayment) {
                this.closePoliedroScannerPayment();
            }
        });

        useEffect(
            () => {
                const posRoot = document.querySelector(".pos");
                posRoot?.classList.toggle(
                    "poliedro-scanner-active",
                    this.isPoliedroScannerLayout
                );
                posRoot?.classList.toggle(
                    "poliedro-scanner-payment-active",
                    this.isPoliedroScannerLayout && this.isPoliedroScannerPayment
                );
                return () => {
                    posRoot?.classList.remove("poliedro-scanner-active");
                    posRoot?.classList.remove("poliedro-scanner-payment-active");
                };
            },
            () => [this.isPoliedroScannerLayout, this.isPoliedroScannerPayment]
        );

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

    get poliedroScannerSearchResults() {
        if (!this.searchWord) {
            return [];
        }
        return this.pos.productsToDisplay.slice(0, 10);
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

    get showPoliedroScannerStock() {
        return this.pos.config.poliedro_scanner_show_stock !== false;
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

    poliedroScannerSearchPrice(product) {
        const pricelist = this.currentOrder?.pricelist_id || this.pos.config.pricelist_id;
        return this._poliedroScannerCurrency(product.getPrice(pricelist, 1));
    },

    async addPoliedroScannerSearchProduct(product) {
        await this.addProductToOrder(product);
        this.pos.searchProductWord = "";
    },

    clearPoliedroScannerSearch() {
        this.pos.searchProductWord = "";
    },

    togglePoliedroScannerLayout() {
        if (this.currentOrder?.uiState) {
            this.currentOrder.uiState.poliedro_scanner_payment_active = false;
        }
        this.poliedroScannerState.active = !this.poliedroScannerState.active;
        this.poliedroScannerState.showNumpad = false;
        this.poliedroScannerState.payment = false;
        this.numberBuffer.reset();
    },

    onPoliedroScannerGlobalKeydown(event) {
        if (!this.isPoliedroScannerLayout || this.isPoliedroScannerPayment) {
            return;
        }

        const target = event.target;
        const isEditable =
            target instanceof HTMLInputElement ||
            target instanceof HTMLTextAreaElement ||
            target?.isContentEditable;
        if (isEditable) {
            return;
        }

        const now = performance.now();
        if (event.key !== "Enter") {
            if (!event.ctrlKey && !event.altKey && !event.metaKey && event.key.length === 1) {
                this.poliedroScannerLastKeyboardInputAt = now;
            }
            return;
        }

        // Barcode readers usually emit Enter immediately after the last character.
        // Only a deliberate Enter opens payment, so a scan never advances by accident.
        if (
            event.repeat ||
            now - this.poliedroScannerLastKeyboardInputAt < 150 ||
            this.currentOrder?.isEmpty()
        ) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();
        this.openPoliedroScannerPayment();
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
        order.uiState.poliedro_scanner_payment_active = true;
        this.poliedroScannerState.payment = true;
        this.pos.searchProductWord = "";
        document.querySelector(".pos-rightheader .input-container input")?.blur();
    },

    closePoliedroScannerPayment() {
        if (this.currentOrder?.uiState) {
            this.currentOrder.uiState.poliedro_scanner_payment_active = false;
        }
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

    editPoliedroScannerLineFromRow(event, line) {
        // Select the row line and open the side numpad to edit it.
        event.stopPropagation();
        if (line.combo_parent_id) {
            line = line.combo_parent_id;
        }
        this.numberBuffer.reset();
        this.pos.selectOrderLine(this.currentOrder, line);
        this.poliedroScannerState.showNumpad = true;
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


patch(PaymentScreen.prototype, {
    get _getNumberBufferConfig() {
        return {
            ...super._getNumberBufferConfig,
            triggerAtEnter: () => this.validatePoliedroScannerOrderWithEnter(),
        };
    },

    validatePoliedroScannerOrderWithEnter() {
        if (
            !this.currentOrder?.uiState?.poliedro_scanner_payment_active ||
            !this.currentOrder.canBeValidated() ||
            this.currentOrder.isRefundInProcess() ||
            this.pos.paymentTerminalInProgress
        ) {
            return;
        }
        return this.validateOrder();
    },
});


patch(Navbar.prototype, {
    handleKeydown(event) {
        // The embedded payment screen shares ProductScreen's navbar. During
        // payment, numeric keys belong exclusively to PaymentScreen's buffer.
        if (this.pos.getOrder()?.uiState?.poliedro_scanner_payment_active) {
            this.bufferedInput = "";
            clearTimeout(this.timeout);
            return;
        }
        return super.handleKeydown(...arguments);
    },

    get poliedroScannerNavbarCustomer() {
        return this.pos.getOrder()?.getPartner();
    },

    get poliedroScannerNavbarCreditInfo() {
        const partner = this.poliedroScannerNavbarCustomer;
        if (!partner?.pos_credit_limit_enabled) {
            return false;
        }
        return {
            credit_limit: partner.pos_credit_limit_amount || 0,
            used_credit: partner.pos_credit_used_amount || 0,
            available_credit: partner.pos_credit_available_amount || 0,
        };
    },

    get poliedroScannerNavbarTotal() {
        const order = this.pos.getOrder();
        const currencyId = order?.currency?.id || this.pos.currency.id;
        return scannerCurrency(order?.priceIncl, currencyId);
    },

    togglePoliedroScannerNavbarInvoice() {
        const order = this.pos.getOrder();
        if (order?.isToInvoice && order?.setToInvoice) {
            order.setToInvoice(!order.isToInvoice());
        }
    },

    showPoliedroClassicLayout() {
        window.dispatchEvent(new CustomEvent("poliedro-scanner-show-classic"));
    },

    closePoliedroScannerNavbarPayment() {
        window.dispatchEvent(new CustomEvent("poliedro-scanner-close-payment"));
    },
});
