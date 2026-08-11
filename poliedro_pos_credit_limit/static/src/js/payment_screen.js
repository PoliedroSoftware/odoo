/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";


patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.poliedroCreditState = useState({
            partnerId: false,
            info: false,
        });
    },

    get hasPayLaterPaymentMethod() {
        return this.payment_methods_from_config.some((method) => method.type === "pay_later");
    },

    get poliedroCreditInfo() {
        const partner = this.currentOrder?.getPartner();
        if (!partner) {
            return false;
        }
        if (
            this.poliedroCreditState.partnerId === partner.id &&
            this.poliedroCreditState.info
        ) {
            return this.poliedroCreditState.info;
        }
        return {
            is_limited: Boolean(partner.pos_credit_limit_enabled),
            feature_enabled: true,
            credit_limit: partner.pos_credit_limit_amount || 0,
            used_credit: partner.pos_credit_used_amount || 0,
            available_credit: partner.pos_credit_available_amount || 0,
        };
    },

    _isPayLaterPaymentMethod(paymentMethod) {
        return paymentMethod?.type === "pay_later";
    },

    _payLaterAmount(excludedLine = false) {
        return this.paymentLines
            .filter(
                (line) =>
                    line !== excludedLine &&
                    this._isPayLaterPaymentMethod(line.payment_method_id)
            )
            .reduce((total, line) => total + line.getAmount(), 0);
    },

    async _refreshPoliedroCreditInfo() {
        const partner = this.currentOrder.getPartner();
        if (!partner) {
            return false;
        }
        const backendOrderId = Number.isInteger(this.currentOrder.id)
            ? this.currentOrder.id
            : false;
        const info = await this.orm.call("res.partner", "get_pos_credit_info", [
            partner.id,
            this.pos.company.id,
            backendOrderId,
        ]);
        this.poliedroCreditState.partnerId = partner.id;
        this.poliedroCreditState.info = info;
        return info;
    },

    _showCreditDialog(title, body) {
        this.dialog.add(AlertDialog, { title, body });
    },

    async addNewPaymentLine(paymentMethod) {
        if (!this._isPayLaterPaymentMethod(paymentMethod) || this.isRefundOrder) {
            return super.addNewPaymentLine(...arguments);
        }

        if (!this.currentOrder.getPartner()) {
            this._showCreditDialog(
                _t("Cliente requerido"),
                _t("Seleccione un cliente antes de usar Cuenta de cliente.")
            );
            return false;
        }

        let info;
        try {
            info = await this._refreshPoliedroCreditInfo();
        } catch {
            this._showCreditDialog(
                _t("No fue posible consultar el cupo"),
                _t("Verifique la conexión con Odoo antes de registrar un pago a crédito.")
            );
            return false;
        }

        const remainingCredit = info.is_limited
            ? Math.max(info.available_credit - this._payLaterAmount(), 0)
            : Infinity;
        if (info.is_limited && remainingCredit <= 0) {
            this._showCreditDialog(
                _t("Cupo agotado"),
                _t("El cliente no tiene saldo disponible para comprar a crédito.")
            );
            return false;
        }

        const added = await super.addNewPaymentLine(...arguments);
        if (added && info.is_limited && this.selectedPaymentLine.amount > remainingCredit) {
            this.selectedPaymentLine.setAmount(remainingCredit);
            this.numberBuffer.set(remainingCredit.toString());
            this.notification.add(
                _t("Se aplicó únicamente el saldo de crédito disponible."),
                { type: "warning" }
            );
        }
        return added;
    },

    updateSelectedPaymentline(amount = false) {
        super.updateSelectedPaymentline(...arguments);
        const line = this.selectedPaymentLine;
        const info = this.poliedroCreditInfo;
        if (
            !line ||
            !info?.is_limited ||
            this.isRefundOrder ||
            !this._isPayLaterPaymentMethod(line.payment_method_id)
        ) {
            return;
        }

        const maxForLine = Math.max(
            info.available_credit - this._payLaterAmount(line),
            0
        );
        if (line.getAmount() > maxForLine) {
            line.setAmount(maxForLine);
            this.numberBuffer.set(maxForLine.toString());
            this.notification.add(
                _t("El valor fue ajustado al cupo disponible del cliente."),
                { type: "warning" }
            );
        }
    },

    async validateOrder(isForceValidate = false) {
        const creditAmount = this._payLaterAmount();
        if (creditAmount > 0 && !this.isRefundOrder) {
            if (!this.currentOrder.getPartner()) {
                this._showCreditDialog(
                    _t("Cliente requerido"),
                    _t("Seleccione un cliente para completar el pago a crédito.")
                );
                return;
            }

            let info;
            try {
                info = await this._refreshPoliedroCreditInfo();
            } catch {
                this._showCreditDialog(
                    _t("No fue posible validar el cupo"),
                    _t("La venta a crédito no puede confirmarse sin conexión con Odoo.")
                );
                return;
            }

            const rounding = this.pos.currency.rounding || 0.01;
            if (info.is_limited && creditAmount - info.available_credit >= rounding / 2) {
                this._showCreditDialog(
                    _t("Cupo insuficiente"),
                    _t("El pago a crédito supera el saldo disponible del cliente.")
                );
                return;
            }

            this.currentOrder.poliedro_credit_limit_snapshot = info.credit_limit;
            this.currentOrder.poliedro_credit_used_before_snapshot = info.used_credit;
            this.currentOrder.poliedro_credit_payment_snapshot = creditAmount;
            this.currentOrder.poliedro_credit_available_after_snapshot = info.is_limited
                ? Math.max(info.available_credit - creditAmount, 0)
                : 0;
        }
        return super.validateOrder(...arguments);
    },
});
