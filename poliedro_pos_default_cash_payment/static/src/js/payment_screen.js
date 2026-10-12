/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async onMounted() {
        await super.onMounted(...arguments);

        // Preserve existing or previously selected payments. Odoo already
        // creates the line when there is only one configured method.
        if (this.paymentLines.length || this.currentOrder?.isEmpty()) {
            return;
        }

        // If several cash methods exist, their configured sequence determines
        // which one is used as the default.
        const cashMethod = this.payment_methods_from_config.find(
            (paymentMethod) => paymentMethod.type === "cash"
        );
        if (cashMethod) {
            await this.addNewPaymentLine(cashMethod);
        }
    },
});
