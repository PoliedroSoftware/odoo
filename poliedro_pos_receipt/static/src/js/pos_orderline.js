import { formatCurrency } from "@web/core/currency";
import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

const receiptCurrency = (amount, currencyId) =>
    formatCurrency(amount, currencyId, { digits: [1, 0], minDigits: 0 });

patch(PosOrderline.prototype, {
    get poliedroCurrencyDisplaySubtotal() {
        // The line subtotal on the thermal invoice represents the amount
        // charged to the customer, including the line taxes.
        return receiptCurrency(this.priceIncl, this.currency.id);
    },

    get poliedroCurrencyDisplayTaxAmount() {
        return receiptCurrency(this.priceIncl - this.priceExcl, this.currency.id);
    },
});

// Keep the accounting currency precision unchanged and remove decimals only
// from the printed POS receipt.
patch(OrderReceipt.prototype, {
    formatCurrency(amount) {
        return receiptCurrency(amount, this.order.currency.id);
    },
});
