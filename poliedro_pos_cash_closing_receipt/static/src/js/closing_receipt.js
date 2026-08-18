import { ClosePosPopup } from "@point_of_sale/app/components/popups/closing_popup/closing_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { formatDateTime } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { renderToElement } from "@web/core/utils/render";

const { DateTime } = luxon;

patch(ClosePosPopup.prototype, {
    getInitialState() {
        return {
            ...super.getInitialState(...arguments),
            poliedroClosingPrinting: false,
        };
    },

    poliedroParseClosingAmount(value, fallback = 0) {
        if (this.env.utils.isValidFloat(value)) {
            return this.env.utils.parseValidFloat(value);
        }
        return fallback;
    },

    get poliedroClosingPaymentRows() {
        const rows = [];

        if (this.pos.config.cash_control) {
            const cash = this.props.default_cash_details;
            const counted = this.poliedroParseClosingAmount(
                this.state.payments[cash.id]?.counted,
                0
            );
            rows.push({
                id: `cash-${cash.id}`,
                name: cash.name,
                expected: cash.amount,
                counted,
                difference: counted - cash.amount,
                isCash: true,
            });
        }

        for (const paymentMethod of this.props.non_cash_payment_methods) {
            const requiresCount = paymentMethod.type === "bank" && paymentMethod.number !== 0;
            const counted = requiresCount
                ? this.poliedroParseClosingAmount(
                      this.state.payments[paymentMethod.id]?.counted,
                      paymentMethod.amount
                  )
                : paymentMethod.amount;
            rows.push({
                id: `payment-${paymentMethod.id}`,
                name: paymentMethod.name,
                expected: paymentMethod.amount,
                counted,
                difference: counted - paymentMethod.amount,
                isCash: false,
            });
        }

        return rows;
    },

    poliedroGetClosingReceiptData() {
        const paymentRows = this.poliedroClosingPaymentRows;
        const cash = this.props.default_cash_details;
        const denominationRows = Object.entries(this.moneyDetails || {})
            .map(([value, quantity]) => ({
                value: Number(value),
                quantity: Number(quantity) || 0,
                subtotal: Number(value) * (Number(quantity) || 0),
            }))
            .filter((row) => row.quantity > 0)
            .sort((left, right) => right.value - left.value);
        const totals = paymentRows.reduce(
            (result, row) => {
                result.expected += row.expected;
                result.counted += row.counted;
                result.difference += row.difference;
                return result;
            },
            { expected: 0, counted: 0, difference: 0 }
        );

        return {
            company: this.pos.company,
            title: this.pos.config.poliedro_receipt_title || this.pos.company?.name,
            posName: this.pos.config.name,
            sessionName: this.pos.session.name || this.pos.session.display_name,
            cashierName: this.pos.getCashier()?.name || "",
            date: formatDateTime(DateTime.now()),
            orders: this.props.orders_details.quantity,
            salesTotal: this.props.orders_details.amount,
            cashControl: this.pos.config.cash_control,
            cash: this.pos.config.cash_control
                ? {
                      name: cash.name,
                      opening: cash.opening,
                      paymentAmount: cash.payment_amount,
                      expected: cash.amount,
                      counted: paymentRows.find((row) => row.isCash)?.counted || 0,
                      difference: paymentRows.find((row) => row.isCash)?.difference || 0,
                  }
                : null,
            moves: this.pos.config.cash_control ? this.cashMoveData.moves : [],
            movesTotal: this.pos.config.cash_control ? this.cashMoveData.total : 0,
            denominationRows,
            paymentRows,
            totals,
            openingNotes: this.props.opening_notes,
            closingNotes: this.state.notes,
            footer: this.pos.config.poliedro_receipt_footer,
            formatCurrency: this.env.utils.formatCurrency,
        };
    },

    async printPoliedroCashClosing() {
        if (!this.hardwareProxy.printer) {
            this.dialog.add(AlertDialog, {
                title: _t("Impresora no disponible"),
                body: _t("No hay una impresora IoT conectada a este punto de venta."),
            });
            return;
        }
        if (!this.canConfirm()) {
            this.dialog.add(AlertDialog, {
                title: _t("Conteo incompleto"),
                body: _t("Complete los valores contados antes de imprimir el arqueo."),
            });
            return;
        }

        this.state.poliedroClosingPrinting = true;
        try {
            const receipt = renderToElement(
                "poliedro_pos_cash_closing_receipt.CashClosingReceipt",
                this.poliedroGetClosingReceiptData()
            );
            const { successful, message } = await this.hardwareProxy.printer.printReceipt(receipt);
            if (!successful) {
                this.dialog.add(AlertDialog, {
                    title: message?.title || _t("No se pudo imprimir"),
                    body:
                        message?.body ||
                        _t("Revise la conexión de la impresora térmica e inténtelo nuevamente."),
                });
                return;
            }
            this.env.services.notification.add(_t("Arqueo enviado a la impresora de 80 mm."), {
                type: "success",
            });
        } catch (error) {
            this.dialog.add(AlertDialog, {
                title: _t("Error al imprimir el arqueo"),
                body:
                    error?.message ||
                    _t("No fue posible preparar el comprobante del arqueo de caja."),
            });
        } finally {
            this.state.poliedroClosingPrinting = false;
        }
    },
});
