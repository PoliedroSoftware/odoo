/** @odoo-module **/

import { formatCurrency } from "@web/core/currency";
import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";


const scannerCurrency = (amount, currencyId) =>
    formatCurrency(amount || 0, currencyId, { digits: [1, 0], minDigits: 0 });


patch(PosOrderline.prototype, {
    get poliedroScannerBarcode() {
        const product = this.product_id;
        return (
            product?.barcode ||
            product?.default_code ||
            product?.product_tmpl_id?.barcode ||
            product?.product_tmpl_id?.default_code ||
            "—"
        );
    },

    get poliedroScannerUnitPrice() {
        return scannerCurrency(this.displayPriceUnitExcl, this.currency.id);
    },

    get poliedroScannerTaxRate() {
        let taxes = this.tax_ids || [];
        if (this.order_id?.fiscal_position_id) {
            taxes = this.order_id.fiscal_position_id.getTaxesAfterFiscalPosition(taxes);
        }
        const labels = taxes.map((tax) => {
                if (["percent", "division"].includes(tax.amount_type)) {
                    return `${tax.amount}%`;
                }
                return tax.name;
            });
        return labels.length ? labels.join(" + ") : "0%";
    },

    get poliedroScannerTaxAmount() {
        return scannerCurrency(this.priceIncl - this.priceExcl, this.currency.id);
    },

    get poliedroScannerDiscount() {
        const discount = this.getDiscount();
        return discount ? `${this.getDiscountStr()}%` : "—";
    },

    get poliedroScannerDiscountAmount() {
        return scannerCurrency(this.prices.discount_amount, this.currency.id);
    },

    get poliedroScannerBaseSubtotal() {
        return scannerCurrency(this.priceExcl, this.currency.id);
    },

    get poliedroScannerLineSubtotal() {
        return scannerCurrency(this.priceIncl, this.currency.id);
    },

    get poliedroScannerStockInfo() {
        // pos_stock_available_online (OCA) adds warehouse_info to the product
        // template payload. Odoo 19 may keep it in `raw` when the field is not
        // declared in the POS model schema.
        const template = this.product_id?.product_tmpl_id;
        const infos = template?.warehouse_info ?? template?.raw?.warehouse_info ?? [];
        const matching = infos.filter(
            (info) => !info.product_id || info.product_id === this.product_id.id
        );
        if (!matching.length) {
            return false;
        }
        const quantity = matching.reduce((total, info) => total + (info.quantity || 0), 0);
        const uomName = this.product_id?.uom_id?.name || "";
        return {
            quantity: Math.round(quantity * 100) / 100,
            uom: uomName,
        };
    },
});
