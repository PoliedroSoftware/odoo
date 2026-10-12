/** @odoo-module **/

import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { HWPrinter } from "@point_of_sale/app/utils/printer/hw_printer";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import {
    Component,
    useExternalListener,
    useState,
} from "@odoo/owl";

import {
    logPosOperation,
    requestPosAuthorization,
} from "@poliedro_pos_authorization_control/js/authorization_service";


const CONNECTED_STATUSES = new Set(["connected", "ready"]);


function actionLabel(action) {
    return {
        cashbox: _t("apertura de cajon"),
        print_receipt: _t("impresion de recibo"),
        status: _t("prueba de impresora"),
    }[action] || _t("accion IoT");
}


patch(HWPrinter.prototype, {
    async sendAction(data) {
        const startedAt = performance.now();
        try {
            const result = await super.sendAction(...arguments);
            window.dispatchEvent(
                new CustomEvent("poliedro-iot-action-result", {
                    detail: {
                        action: data?.action || "",
                        successful: result !== false,
                        latency: Math.round(performance.now() - startedAt),
                        at: Date.now(),
                    },
                })
            );
            return result;
        } catch (error) {
            window.dispatchEvent(
                new CustomEvent("poliedro-iot-action-result", {
                    detail: {
                        action: data?.action || "",
                        successful: false,
                        latency: Math.round(performance.now() - startedAt),
                        at: Date.now(),
                    },
                })
            );
            throw error;
        }
    },
});


export class PoliedroIoTHealth extends Component {
    static template = "poliedro_pos_iot_health.IoTHealth";
    static props = {};

    setup() {
        this.pos = usePos();
        this.hardwareProxy = useService("hardware_proxy");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.connectionInfo = useState(this.hardwareProxy.connectionInfo);
        this.state = useState({
            open: false,
            busy: "",
            lastAction: "",
            lastActionSuccessful: null,
            lastActionLatency: null,
            lastActionAt: null,
            scaleWeight: null,
            scaleCheckedAt: null,
        });
        useExternalListener(document, "keydown", (event) => {
            if (event.key === "Escape" && this.state.open) {
                this.close();
            }
        });
        useExternalListener(window, "poliedro-iot-health-open", () => {
            this.state.open = true;
        });
        useExternalListener(window, "poliedro-iot-action-result", (event) => {
            this.state.lastAction = event.detail?.action || "";
            this.state.lastActionSuccessful = Boolean(event.detail?.successful);
            this.state.lastActionLatency = event.detail?.latency ?? null;
            this.state.lastActionAt = event.detail?.at || Date.now();
        });
    }

    get enabled() {
        return this.pos.config.poliedro_iot_health_enabled !== false && this.pos.config.useProxy;
    }

    get proxyConnected() {
        return this.connectionInfo.status === "connected";
    }

    get printerEnabled() {
        return Boolean(
            this.pos.config.iface_print_via_proxy || this.pos.config.iface_cashdrawer
        );
    }

    get scaleEnabled() {
        return Boolean(this.pos.config.iface_electronic_scale);
    }

    get printerConnected() {
        return Boolean(
            this.proxyConnected &&
            CONNECTED_STATUSES.has(this.connectionInfo.drivers?.printer?.status)
        );
    }

    get scaleConnected() {
        return Boolean(
            this.proxyConnected &&
            CONNECTED_STATUSES.has(this.connectionInfo.drivers?.scale?.status)
        );
    }

    get drawerConnected() {
        return Boolean(this.pos.config.iface_cashdrawer && this.printerConnected);
    }

    get overallState() {
        if (["init", "connecting"].includes(this.connectionInfo.status)) {
            return "checking";
        }
        if (!this.proxyConnected) {
            return "danger";
        }
        if (
            (this.printerEnabled && !this.printerConnected) ||
            (this.scaleEnabled && !this.scaleConnected)
        ) {
            return "warning";
        }
        return "success";
    }

    get overallLabel() {
        return {
            checking: _t("Revisando equipos"),
            danger: _t("IoT sin conexion"),
            warning: _t("Revisar equipos"),
            success: _t("Equipos OK"),
        }[this.overallState];
    }

    get lastActionLabel() {
        if (!this.state.lastAction) {
            return _t("Sin ordenes recientes en esta pantalla");
        }
        return `${actionLabel(this.state.lastAction)} - ${this.state.lastActionLatency || 0} ms`;
    }

    get lastActionTime() {
        if (!this.state.lastActionAt) {
            return "";
        }
        return new Intl.DateTimeFormat("es-CO", {
            hour: "numeric",
            minute: "2-digit",
            second: "2-digit",
        }).format(new Date(this.state.lastActionAt));
    }

    get formattedScaleWeight() {
        if (this.state.scaleWeight === null) {
            return "";
        }
        return `${new Intl.NumberFormat("es-CO", {
            minimumFractionDigits: 3,
            maximumFractionDigits: 3,
        }).format(this.state.scaleWeight)} kg`;
    }

    toggle() {
        this.state.open = !this.state.open;
    }

    close() {
        this.state.open = false;
    }

    async reconnect() {
        if (this.state.busy) {
            return;
        }
        this.state.busy = "reconnect";
        try {
            await Promise.race([
                this.pos.connectToProxy(),
                new Promise((_, reject) =>
                    setTimeout(() => reject(new Error("timeout")), 8000)
                ),
            ]);
            this.notification.add(_t("Conexion IoT actualizada."), { type: "success" });
        } catch {
            this.notification.add(
                _t("No fue posible reconectar. Revise el servicio IoT y la red local."),
                { type: "danger" }
            );
        } finally {
            this.state.busy = "";
        }
    }

    async testPrinter() {
        if (this.state.busy || !this.printerConnected || !this.hardwareProxy.printer) {
            this.notification.add(_t("La impresora no esta disponible."), { type: "warning" });
            return;
        }
        this.state.busy = "printer";
        try {
            const accepted = await this.hardwareProxy.printer.sendAction({
                action: "status",
                action_unique_id: `poliedro-health-printer-${Date.now()}`,
            });
            if (accepted === false) {
                throw new Error("not accepted");
            }
            this.notification.add(_t("Orden de prueba enviada a la impresora."), {
                type: "success",
            });
        } catch {
            this.notification.add(_t("La prueba de impresion fallo."), { type: "danger" });
        } finally {
            this.state.busy = "";
        }
    }

    async testScale() {
        if (this.state.busy || !this.scaleConnected) {
            this.notification.add(_t("La bascula no esta disponible."), { type: "warning" });
            return;
        }
        this.state.busy = "scale";
        try {
            const result = await this.hardwareProxy.message("scale_read");
            const weight = Number(result?.weight ?? result);
            if (!Number.isFinite(weight)) {
                throw new Error("invalid weight");
            }
            this.state.scaleWeight = weight;
            this.state.scaleCheckedAt = Date.now();
            this.notification.add(_t("Lectura de bascula recibida."), { type: "success" });
        } catch {
            this.notification.add(_t("No fue posible leer la bascula."), { type: "danger" });
        } finally {
            this.state.busy = "";
        }
    }

    async testDrawer() {
        if (this.state.busy || !this.drawerConnected || !this.hardwareProxy.printer) {
            this.notification.add(_t("El cajon no esta disponible."), { type: "warning" });
            return;
        }
        let authorization = { authorized: true };
        if (
            this.pos.config.poliedro_authorization_enabled &&
            this.pos.config.poliedro_auth_cashbox
        ) {
            authorization = await requestPosAuthorization(this, {
                operationLabel: _t("Probar la apertura del cajon desde el monitor IoT"),
            });
            if (!authorization?.authorized) {
                return;
            }
        }
        this.state.busy = "drawer";
        try {
            const accepted = await this.hardwareProxy.printer.openCashbox();
            if (accepted === false) {
                throw new Error("not accepted");
            }
            await logPosOperation(
                this,
                "cashbox_open",
                { reason: _t("Prueba desde el monitor de salud IoT") },
                authorization
            );
            this.notification.add(_t("Orden de apertura enviada al cajon."), {
                type: "success",
            });
        } catch {
            this.notification.add(_t("La prueba del cajon fallo."), { type: "danger" });
        } finally {
            this.state.busy = "";
        }
    }
}


Navbar.components = {
    ...Navbar.components,
    PoliedroIoTHealth,
};


patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate = false) {
        const config = this.pos.config;
        const info = this.hardwareProxy.connectionInfo;
        const printerUnavailable =
            config.poliedro_iot_health_enabled !== false &&
            config.poliedro_iot_health_warn_before_validation !== false &&
            config.iface_print_auto &&
            config.iface_print_via_proxy &&
            !(
                info.status === "connected" &&
                CONNECTED_STATUSES.has(info.drivers?.printer?.status)
            );
        const warningAlreadyAccepted = Boolean(
            this.currentOrder.uiState?.poliedro_iot_health_warning_accepted
        );

        if (!isForceValidate && printerUnavailable && !warningAlreadyAccepted) {
            const confirmed = await ask(this.dialog, {
                title: _t("Impresora no disponible"),
                body: _t(
                    "La venta puede confirmarse, pero el recibo no se imprimira automaticamente y el cajon podria no abrir. Desea continuar?"
                ),
            });
            if (!confirmed) {
                window.dispatchEvent(new CustomEvent("poliedro-iot-health-open"));
                return;
            }
            this.currentOrder.uiState.poliedro_iot_health_warning_accepted = true;
        }

        return super.validateOrder(...arguments);
    },
});
