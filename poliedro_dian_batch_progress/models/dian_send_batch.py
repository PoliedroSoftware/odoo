from odoo import api, fields, models


class PoliedroDianSendBatch(models.Model):
    _name = "poliedro.dian.send.batch"
    _description = "Lote de seguimiento de envío DIAN"
    _order = "create_date desc, id desc"

    company_id = fields.Many2one("res.company", required=True, index=True)
    move_ids = fields.Many2many(
        "account.move",
        "poliedro_dian_batch_move_rel",
        "batch_id",
        "move_id",
        string="Facturas",
        required=True,
    )
    create_date = fields.Datetime(readonly=True)

    @api.model
    def get_navbar_progress(self):
        allowed_company_ids = self.env.companies.ids
        batches = self.sudo().search(
            [("company_id", "in", allowed_company_ids)],
            order="create_date desc, id desc",
            limit=20,
        )
        if not batches:
            return False
        batch = batches.filtered(lambda item: any(move.sending_data for move in item.move_ids))[:1]
        batch = batch or batches[:1]
        moves = batch.move_ids
        rows = []
        counts = {"accepted": 0, "queued": 0, "pending": 0, "failed": 0}
        for move in moves:
            documents = move.l10n_co_dian_document_ids.sorted(
                key=lambda doc: (doc.datetime or doc.create_date, doc.id), reverse=True
            )
            doc = documents[:1]
            if doc and doc.state == "invoice_accepted":
                status = "accepted"
                reason = "Aceptada por DIAN"
            elif doc and doc.state == "invoice_rejected":
                status = "failed"
                message = doc.message_json or {}
                reason = message.get("errors") or message.get("status") or "Rechazada por DIAN"
            elif doc and doc.state == "invoice_sending_failed":
                status = "failed"
                message = doc.message_json or {}
                reason = message.get("errors") or message.get("status") or "Error al conectar con DIAN"
            elif doc and doc.state == "invoice_pending":
                status = "pending"
                reason = "Enviada; DIAN aún no confirma el resultado"
            elif move.sending_data:
                status = "queued"
                reason = "En cola para envío"
            else:
                status = "failed"
                reason = "No se recibió respuesta de DIAN"
            counts[status] += 1
            if status == "failed":
                if isinstance(reason, list):
                    reason = "; ".join(str(item) for item in reason)
                elif isinstance(reason, dict):
                    reason = "; ".join(str(value) for value in reason.values())
                rows.append({"name": move.name, "reason": str(reason)[:500]})

        total = len(moves)
        completed = counts["accepted"] + counts["failed"]
        return {
            "id": batch.id,
            "company": batch.company_id.name,
            "total": total,
            "accepted": counts["accepted"],
            "queued": counts["queued"],
            "pending": counts["pending"],
            "failed": counts["failed"],
            "completed": completed,
            "percent": round(completed * 100 / total) if total else 100,
            "errors": rows[:12],
            "is_active": bool(counts["queued"] or counts["pending"]),
        }
