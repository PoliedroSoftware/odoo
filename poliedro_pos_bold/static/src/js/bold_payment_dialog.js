import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

export class BoldPaymentDialog extends ConfirmationDialog {
    static template = "poliedro_pos_bold.BoldPaymentDialog";
    static props = {
        ...ConfirmationDialog.props,
        amount: String,
        applink: String,
        qrCode: String,
        reference: String,
    };
    static defaultProps = {
        ...ConfirmationDialog.defaultProps,
        title: _t("Cobro con Bold NEO"),
        confirmLabel: _t("El pago fue aprobado"),
        cancelLabel: _t("Cancelar cobro"),
        confirmClass: "btn-success",
    };
}
