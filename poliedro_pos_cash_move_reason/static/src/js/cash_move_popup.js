/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CashMovePopup } from "@point_of_sale/app/components/popups/cash_move_popup/cash_move_popup";

patch(CashMovePopup.prototype, {
    setup() {
        super.setup(...arguments);
        this.state.poliedroReasonId = "";
        this.state.poliedroDetail = "";
        this.state.poliedroReasons = [];
        this.loadPoliedroReasons();
    },
    async loadPoliedroReasons() {
        this.state.poliedroReasons = await this.pos.data.call(
            "poliedro.pos.cash.move.reason", "get_pos_reasons", [this.state.type, this.pos.config.id]
        );
    },
    async onClickButton(type) {
        super.onClickButton(type);
        this.state.poliedroReasonId = "";
        await this.loadPoliedroReasons();
    },
    onPoliedroReasonChange(event) {
        this.state.poliedroReasonId = event.target.value;
        this.updatePoliedroReason();
    },
    updatePoliedroReason() {
        const selected = this.state.poliedroReasons.find(
            (reason) => String(reason.id) === String(this.state.poliedroReasonId)
        );
        const parts = [selected?.name, this.state.poliedroDetail.trim()].filter(Boolean);
        this.state.reason = parts.join(" - ");
    },
    isValidCashMove() {
        return super.isValidCashMove(...arguments) && Boolean(this.state.poliedroReasonId);
    },
    _prepareTryCashInOutPayload(type, amount, reason, partnerId, extras) {
        return super._prepareTryCashInOutPayload(type, amount, reason, partnerId, {
            ...extras,
            poliedro_reason_id: Number(this.state.poliedroReasonId),
        });
    },
});
