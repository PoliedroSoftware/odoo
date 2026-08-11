/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosData } from "@point_of_sale/app/services/data_service";
import { HardwareProxy } from "@point_of_sale/app/services/hardware_proxy_service";
import { PosStore } from "@point_of_sale/app/services/pos_store";


function normalizedProxyHost(proxyAddress) {
    if (!proxyAddress) {
        return "";
    }
    try {
        const value = proxyAddress.includes("://") ? proxyAddress : `http://${proxyAddress}`;
        return new URL(value).host;
    } catch {
        return proxyAddress;
    }
}


patch(PosData.prototype, {
    async loadInitialData(...args) {
        const localData = await this.getCachedServerDataFromIndexedDB();
        const cachedConfig = localData?.["pos.config"]?.[0];
        const cachedProxyHost = normalizedProxyHost(cachedConfig?.proxy_ip);

        if (
            (cachedProxyHost && cachedProxyHost !== window.location.host) ||
            cachedConfig?.iface_print_via_proxy !== true
        ) {
            await this.resetIndexedDB();
            await this.initIndexedDB(this.relations);
        }

        return super.loadInitialData(...args);
    },
});


patch(HardwareProxy.prototype, {
    async connect(...args) {
        // Always attach the hardware printer before the same-origin handshake.
        this.connectToPrinter();
        return super.connect(...args);
    },
});


patch(PosStore.prototype, {
    get printOptions() {
        // Never report a browser window.print fallback as an IoT print success.
        return { webPrintFallback: false };
    },
});
