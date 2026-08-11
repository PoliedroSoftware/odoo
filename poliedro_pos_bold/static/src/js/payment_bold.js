import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PaymentInterface } from "@point_of_sale/app/utils/payment/payment_interface";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { register_payment_method } from "@point_of_sale/app/services/pos_store";
import { generateQRCodeDataUrl } from "@point_of_sale/utils";
import { BoldPaymentDialog } from "./bold_payment_dialog";

export class PaymentBold extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.activePaymentUuid = null;
    }

    _getPaymentLine(uuid) {
        return this.pos.getOrder()?.payment_ids.find((line) => line.uuid === uuid);
    }

    _getReference(line) {
        const compactUuid = String(line.uuid || "").replaceAll("-", "").toUpperCase();
        return `OD${compactUuid.slice(0, 22)}`;
    }

    _getDescription(order) {
        const orderName = order?.name && order.name !== "/" ? order.name : "Venta Odoo POS";
        return String(orderName).replace(/[\r\n]+/g, " ").slice(0, 20);
    }

    _showError(error) {
        const message = error?.data?.message || error?.message || String(error);
        this.env.services.dialog.add(AlertDialog, {
            title: _t("No fue posible iniciar el cobro Bold"),
            body: message,
        });
    }

    async sendPaymentRequest(uuid) {
        await super.sendPaymentRequest(...arguments);
        const order = this.pos.getOrder();
        const line = this._getPaymentLine(uuid);
        if (!order || !line) {
            return false;
        }

        this.activePaymentUuid = uuid;
        line.setPaymentStatus("waitingCapture");
        try {
            const result = await this.env.services.orm.call(
                "pos.payment.method",
                "bold_create_applink",
                [
                    [line.payment_method_id.id],
                    line.amount,
                    this._getReference(line),
                    this._getDescription(order),
                ]
            );
            const qrCode = generateQRCodeDataUrl(result.url, { width: 280, height: 280 });
            const formattedAmount = this.env.utils.formatCurrency(line.amount);

            line.setPaymentStatus("waitingCard");
            line.qrPaymentData = {
                name: line.payment_method_id.name,
                amount: formattedAmount,
                qrCode,
            };

            const approved = await ask(
                this.env.services.dialog,
                {
                    amount: formattedAmount,
                    applink: result.url,
                    qrCode,
                    reference: result.reference,
                },
                {},
                BoldPaymentDialog
            );

            line.qrPaymentData = null;
            if (!approved) {
                return false;
            }

            line.transaction_id = result.reference;
            line.payment_ref_no = result.reference;
            line.payment_method_payment_mode = "BOLD_NEO_APPLINK";
            line.setReceiptInfo(`Bold NEO\nReferencia: ${result.reference}\n`);
            return true;
        } catch (error) {
            line.qrPaymentData = null;
            this._showError(error);
            return false;
        } finally {
            this.activePaymentUuid = null;
        }
    }

    async sendPaymentCancel() {
        await super.sendPaymentCancel(...arguments);
        return true;
    }
}

register_payment_method("bold", PaymentBold);
