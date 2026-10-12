/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { requestPosAuthorization, logPosOperation } from "./authorization_service";

patch(PosStore.prototype, {
    async cashMove() {
        let authorization = { authorized: true };
        if (this.config.poliedro_authorization_enabled && this.config.poliedro_auth_cashbox) {
            authorization = await requestPosAuthorization(this, {
                operationLabel: _t("Abrir el cajón para una entrada o salida de efectivo"),
            });
            if (!authorization?.authorized) return;
        }
        return await super.cashMove(...arguments);
    },
    async setDiscountFromUI(line, value) {
        const discount = Number(value || 0);
        const previous = Number(line.getDiscount?.() || 0);
        const threshold = Number(this.config.poliedro_auth_discount_threshold || 0);
        let authorization = { authorized: true };
        if (
            this.config.poliedro_authorization_enabled &&
            discount > threshold &&
            discount !== previous
        ) {
            authorization = await requestPosAuthorization(this, {
                operationLabel: _t("Aplicar descuento de %s%%", discount),
            });
            if (!authorization?.authorized) {
                return false;
            }
        }
        await super.setDiscountFromUI(line, value);
        if (discount !== previous) {
            await logPosOperation(this, "discount", {
                product: line.product_id,
                previousValue: previous,
                newValue: discount,
            }, authorization);
        }
        return true;
    },
});

patch(OrderSummary.prototype, {
    async updateSelectedOrderline({ buffer, key }) {
        const line = this.currentOrder?.getSelectedOrderline?.();
        if (line && buffer === null && this.pos.numpadMode === "quantity") {
            const authorization = await authorizeLineDeletion(this, line);
            if (!authorization?.authorized) {
                this.numberBuffer.reset();
                return;
            }
            const product = line.product_id;
            const quantity = line.getQuantity();
            const result = await super.updateSelectedOrderline(...arguments);
            await logPosOperation(this, "line_delete", {
                product, previousValue: quantity, newValue: 0,
            }, authorization);
            return result;
        }
        return await super.updateSelectedOrderline(...arguments);
    },
    async setLinePrice(line, price) {
        const previous = Number(line.getUnitPrice?.() ?? line.price_unit ?? 0);
        const next = Number(price || 0);
        let authorization = { authorized: true };
        if (
            this.pos.config.poliedro_authorization_enabled &&
            this.pos.config.poliedro_auth_price_change &&
            previous !== next
        ) {
            authorization = await requestPosAuthorization(this, {
                operationLabel: _t("Cambiar precio de %s", line.getFullProductName?.() || line.product_id?.display_name),
            });
            if (!authorization?.authorized) {
                return false;
            }
        }
        await super.setLinePrice(line, price);
        if (previous !== next) {
            await logPosOperation(this, "price_change", {
                product: line.product_id,
                previousValue: previous,
                newValue: next,
            }, authorization);
        }
        return true;
    },
});

async function authorizeLineDeletion(component, line) {
    if (!component.pos.config.poliedro_authorization_enabled || !component.pos.config.poliedro_auth_line_delete) {
        return { authorized: true };
    }
    return requestPosAuthorization(component, {
        operationLabel: _t("Eliminar %s de la venta", line.getFullProductName?.() || line.product_id?.display_name),
    });
}

patch(ProductScreen.prototype, {
    async updatePoliedroScannerLineQty(event, line) {
        const value = Number(event.target.value);
        if (event.target.value && value <= 0) {
            event.stopPropagation();
            line = line.combo_parent_id || line;
            const authorization = await authorizeLineDeletion(this, line);
            if (!authorization?.authorized) {
                event.target.value = line.getQuantity();
                return;
            }
            const product = line.product_id;
            const quantity = line.getQuantity();
            this.numberBuffer.reset();
            this.currentOrder.removeOrderline(line);
            this.poliedroScannerState.showNumpad = false;
            await logPosOperation(this, "line_delete", {
                product, previousValue: quantity, newValue: 0,
            }, authorization);
            return;
        }
        return super.updatePoliedroScannerLineQty(...arguments);
    },
    async removePoliedroScannerLineFromRow(event, line) {
        event.stopPropagation();
        line = line.combo_parent_id || line;
        const authorization = await authorizeLineDeletion(this, line);
        if (!authorization?.authorized) return;
        this.numberBuffer.reset();
        const product = line.product_id;
        const quantity = line.getQuantity();
        this.currentOrder.removeOrderline(line);
        this.poliedroScannerState.showNumpad = false;
        await logPosOperation(this, "line_delete", {
            product, previousValue: quantity, newValue: 0,
        }, authorization);
    },
    async removePoliedroScannerLine() {
        if (!this.poliedroScannerSelectedLine) return;
        let line = this.poliedroScannerSelectedLine;
        line = line.combo_parent_id || line;
        const authorization = await authorizeLineDeletion(this, line);
        if (!authorization?.authorized) return;
        this.numberBuffer.reset();
        const product = line.product_id;
        const quantity = line.getQuantity();
        this.currentOrder.removeOrderline(line);
        this.poliedroScannerState.showNumpad = false;
        await logPosOperation(this, "line_delete", {
            product, previousValue: quantity, newValue: 0,
        }, authorization);
    },
});

patch(TicketScreen.prototype, {
    async onDoRefund() {
        let authorization = { authorized: true };
        if (this.pos.config.poliedro_authorization_enabled && this.pos.config.poliedro_auth_refund) {
            authorization = await requestPosAuthorization(this, {
                operationLabel: _t("Procesar devolución de productos"),
            });
            if (!authorization?.authorized) return;
        }
        const result = await super.onDoRefund(...arguments);
        await logPosOperation(this, "refund", {}, authorization);
        return result;
    },
    async onDeleteOrder(order) {
        const reference = order?.pos_reference || order?.name || order?.uuid;
        const result = await super.onDeleteOrder(...arguments);
        await logPosOperation(this, "order_cancel", {
            reason: _t("Orden eliminada desde la pantalla de órdenes"),
            previousValue: reference,
        });
        return result;
    },
});

patch(PaymentScreen.prototype, {
    async openCashbox() {
        let authorization = { authorized: true };
        if (this.pos.config.poliedro_authorization_enabled && this.pos.config.poliedro_auth_cashbox) {
            authorization = await requestPosAuthorization(this, {
                operationLabel: _t("Abrir el cajón sin registrar una venta"),
            });
            if (!authorization?.authorized) return;
        }
        this.hardwareProxy.openCashbox();
        await logPosOperation(this, "cashbox_open", {}, authorization);
    },
});
