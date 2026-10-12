/** @odoo-module **/

import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

export class PriceCheckDialog extends Component {
    static template = "poliedro_pos_price_check.PriceCheckDialog";
    static components = { Dialog };
    static props = {
        productName: String,
        barcode: { type: String, optional: true },
        defaultCode: { type: String, optional: true },
        price: String,
        listPrice: String,
        promotion: { type: String, optional: true },
        taxName: { type: String, optional: true },
        taxAmount: { type: String, optional: true },
        availableQuantity: { type: [Number, String], optional: true },
        freeQuantity: { type: [Number, String], optional: true },
        uom: { type: String, optional: true },
        getPayload: Function,
        close: Function,
    };
    add() { this.props.getPayload("add"); this.props.close(); }
    close() { this.props.close(); }
}

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.state.poliedroPriceCheckMode = false;
    },
    togglePoliedroPriceCheck() {
        this.state.poliedroPriceCheckMode = !this.state.poliedroPriceCheckMode;
        this.notification.add(
            this.state.poliedroPriceCheckMode
                ? _t("Consulta de precio activada. Escanee un producto.")
                : _t("Consulta de precio desactivada."),
            { type: this.state.poliedroPriceCheckMode ? "info" : "warning" }
        );
    },
    async showPoliedroPriceCheck(productTemplate, productVariant = false) {
        const order = this.currentOrder;
        const variant = productVariant || productTemplate.product_variant_ids?.[0] || false;
        const info = await this.pos.getProductInfo(productTemplate, 1, 0, variant);
        const currentPrice = productTemplate.getPrice(order.pricelist_id, 1, 0, false, variant || false);
        const listPrice = Number(productTemplate.list_price || currentPrice);
        const promotion = currentPrice < listPrice
            ? _t("Ahorra %s", this.env.utils.formatCurrency(listPrice - currentPrice))
            : "";
        const warehouse = info.productInfo?.warehouses?.[0] || {};
        const result = await makeAwaitable(this.dialog, PriceCheckDialog, {
            productName: variant?.display_name || productTemplate.display_name,
            barcode: variant?.barcode || "",
            defaultCode: variant?.default_code || "",
            price: this.env.utils.formatCurrency(currentPrice),
            listPrice: this.env.utils.formatCurrency(listPrice),
            promotion,
            taxName: info.taxName || _t("Sin impuesto"),
            taxAmount: info.taxAmount,
            availableQuantity: warehouse.available_quantity ?? 0,
            freeQuantity: warehouse.free_qty ?? 0,
            uom: warehouse.uom || productTemplate.uom_id?.name || "",
        });
        if (result === "add") {
            this.state.poliedroPriceCheckMode = false;
            await this.pos.addLineToCurrentOrder(
                variant
                    ? { product_id: variant, product_tmpl_id: productTemplate }
                    : { product_tmpl_id: productTemplate }
            );
        }
    },
    async _barcodeProductAction(code) {
        if (!this.state.poliedroPriceCheckMode) {
            return await super._barcodeProductAction(...arguments);
        }
        const product = await this._getProductByBarcode(code);
        if (!product) {
            this.sound.play("scan-error");
            this.barcodeReader.showNotFoundNotification(code);
            return;
        }
        this.sound.play("beep");
        await this.showPoliedroPriceCheck(product.product_tmpl_id, product);
        this.numberBuffer.reset();
    },
    async addProductToOrder(productTemplate) {
        if (this.state.poliedroPriceCheckMode) {
            return await this.showPoliedroPriceCheck(productTemplate);
        }
        return await super.addProductToOrder(...arguments);
    },
});
