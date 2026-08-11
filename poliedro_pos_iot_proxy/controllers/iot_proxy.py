import base64
import logging

import requests
from werkzeug.exceptions import ServiceUnavailable

from odoo import http
from odoo.http import request


_logger = logging.getLogger(__name__)

IOT_URL_PARAMETER = "poliedro_pos_iot_proxy.iot_url"
DEFAULT_IOT_URL = "http://127.0.0.1:8069"
REQUEST_TIMEOUT = (1, 30)


class PoliedroPosIotProxyController(http.Controller):
    """Keep browser hardware calls on Odoo's origin and forward them locally."""

    def _iot_url(self):
        return request.env["ir.config_parameter"].sudo().get_param(
            IOT_URL_PARAMETER, DEFAULT_IOT_URL
        ).rstrip("/")

    def _call_jsonrpc(self, route, params=None):
        url = f"{self._iot_url()}/hw_proxy/{route}"
        try:
            response = requests.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": params or {},
                    "id": 1,
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("error"):
                raise RuntimeError(payload["error"])
            return payload.get("result")
        except (requests.RequestException, ValueError, RuntimeError) as error:
            _logger.warning("IoT request failed for %s: %s", route, error)
            raise ServiceUnavailable("El IoT local no esta disponible") from error

    @http.route("/hw_proxy/hello", type="http", auth="user", methods=["GET"])
    def hello(self):
        url = f"{self._iot_url()}/hw_proxy/hello"
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            if response.text.strip() != "ping":
                raise ValueError("Unexpected IoT hello response")
        except (requests.RequestException, ValueError) as error:
            _logger.warning("IoT hello failed: %s", error)
            raise ServiceUnavailable("El IoT local no esta disponible") from error

        return request.make_response(
            "ping",
            headers=[
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Cache-Control", "no-store"),
            ],
        )

    @http.route("/hw_proxy/handshake", type="jsonrpc", auth="user", methods=["POST"])
    def handshake(self, **params):
        return self._call_jsonrpc("handshake", params)

    @http.route("/hw_proxy/status_json", type="jsonrpc", auth="user", methods=["POST"])
    def status_json(self, **params):
        return self._call_jsonrpc("status_json", params)

    @http.route("/hw_proxy/scale_read", type="jsonrpc", auth="user", methods=["POST"])
    def scale_read(self, **params):
        return self._call_jsonrpc("scale_read", params)

    @http.route(
        "/hw_proxy/default_printer_action",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def default_printer_action(self, **params):
        data = params.get("data") or {}
        action = data.get("action", "")
        receipt_size = 0
        if action == "print_receipt" and data.get("receipt"):
            try:
                receipt_size = len(base64.b64decode(data["receipt"], validate=False))
            except (TypeError, ValueError):
                receipt_size = -1

        result = self._call_jsonrpc("default_printer_action", params)
        _logger.info(
            "POS IoT action=%s receipt_bytes=%s accepted=%s",
            action,
            receipt_size,
            result,
        )
        return result
