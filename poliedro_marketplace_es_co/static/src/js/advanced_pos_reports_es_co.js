/** @odoo-module **/

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { CategorySummaryPopup } from "@advanced_pos_reports/js/CategoryPopup";
import { LocationSummaryPopup } from "@advanced_pos_reports/js/LocationPopup";
import { OrderSummaryPopup } from "@advanced_pos_reports/js/OrderPopup";
import { PaymentSummaryPopup } from "@advanced_pos_reports/js/PaymentPopup";
import { ProductSummaryPopup } from "@advanced_pos_reports/js/ProductPopup";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

const MARKETPLACE_TERMS = [
    _t("Amount"),
    _t("Cancel"),
    _t("Cancelled"),
    _t("Categories"),
    _t("Category"),
    _t("Category Summary"),
    _t("Close"),
    _t("Confirm"),
    _t("Current Session"),
    _t("Customer"),
    _t("Customers"),
    _t("Date"),
    _t("Done"),
    _t("End Date"),
    _t("End Date:"),
    _t("Invoiced"),
    _t("Location Summary"),
    _t("Locations"),
    _t("Logo"),
    _t("None"),
    _t("Ongoing"),
    _t("Order Ref"),
    _t("Order Summary"),
    _t("Paid"),
    _t("Payment Method"),
    _t("Payment Summary"),
    _t("Print Category Summary"),
    _t("Print Location Summary"),
    _t("Print Order Summary"),
    _t("Print Payment Summary"),
    _t("Print Product Summary"),
    _t("Product"),
    _t("Product Summary"),
    _t("Quantity"),
    _t("Salesperson"),
    _t("Salesperson:"),
    _t("Select status"),
    _t("Served by"),
    _t("Start Date"),
    _t("Start Date:"),
    _t("Status"),
    _t("Summary"),
    _t("Tel:"),
    _t("Total"),
    _t("Total:"),
    _t("Unit"),
    _t("Error"),
    _t("No Data"),
    _t("No Data Available ."),
    _t("No Data Available."),
    _t("Start Date Greater than End Date ."),
    _t("Location Receipt"),
];

// Keep the terms referenced so the asset optimizer cannot discard them.
void MARKETPLACE_TERMS;

function localizedDialog(dialog) {
    return new Proxy(dialog, {
        get(target, property, receiver) {
            if (property === "add") {
                return (component, props = {}, ...args) => {
                    const translatedProps = { ...props };
                    if (typeof translatedProps.title === "string") {
                        translatedProps.title = _t(translatedProps.title);
                    }
                    if (typeof translatedProps.body === "string") {
                        translatedProps.body = _t(translatedProps.body);
                    }
                    return target.add(component, translatedProps, ...args);
                };
            }
            const value = Reflect.get(target, property, receiver);
            return typeof value === "function" ? value.bind(target) : value;
        },
    });
}

function localizePopupDialogs(PopupClass) {
    patch(PopupClass.prototype, {
        setup() {
            super.setup(...arguments);
            this.dialog = localizedDialog(this.dialog);
        },
    });
}

for (const PopupClass of [
    CategorySummaryPopup,
    LocationSummaryPopup,
    OrderSummaryPopup,
    PaymentSummaryPopup,
    ProductSummaryPopup,
]) {
    localizePopupDialogs(PopupClass);
}

patch(ControlButtons.prototype, {
    async onClick() {
        await this.dialog.add(CategorySummaryPopup, {
            title: _t("Category Summary"),
        });
    },

    async onClickLocation() {
        await this.dialog.add(LocationSummaryPopup, {
            title: _t("Location Summary"),
        });
    },

    async onClickOrderSummary() {
        await this.dialog.add(OrderSummaryPopup, {
            title: _t("Order Summary"),
        });
    },

    async onClickPaymentSummary() {
        await this.dialog.add(PaymentSummaryPopup, {
            title: _t("Payment Summary"),
        });
    },

    async onClickProductSummary() {
        await this.dialog.add(ProductSummaryPopup, {
            title: _t("Product Summary"),
        });
    },
});
