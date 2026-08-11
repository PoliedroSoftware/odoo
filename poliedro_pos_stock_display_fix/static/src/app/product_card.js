import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { patch } from "@web/core/utils/patch";

// pos_stock_available_online adds these values to the backend payload without
// declaring them in the POS model schema. Odoo 19 therefore keeps them in
// `config.raw` instead of exposing them directly on the config record.
patch(ProductCard.prototype, {
    get displayProductQuantity() {
        return (
            this.pos.config.display_product_quantity ??
            this.pos.config.raw?.display_product_quantity ??
            false
        );
    },

    get minimumProductQuantityAlert() {
        return (
            this.pos.config.minimum_product_quantity_alert ??
            this.pos.config.raw?.minimum_product_quantity_alert ??
            0
        );
    },
});
