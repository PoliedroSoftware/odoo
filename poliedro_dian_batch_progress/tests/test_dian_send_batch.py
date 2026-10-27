from odoo.tests import TransactionCase


class TestDianSendBatch(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "DIAN Batch Test"})
        cls.company = cls.env.company

    def _new_move(self, name):
        return self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "company_id": self.company.id,
            "ref": name,
        })

    def test_progress_counts_accepted_queued_and_rejected(self):
        accepted = self._new_move("accepted")
        queued = self._new_move("queued")
        rejected = self._new_move("rejected")
        queued.sending_data = {"author_user_id": self.env.user.id}
        self.env["l10n_co_dian.document"].create([
            {"move_id": accepted.id, "state": "invoice_accepted", "message_json": {"status": "Accepted"}},
            {"move_id": rejected.id, "state": "invoice_rejected", "message_json": {"errors": ["Invalid test reason"]}},
        ])
        self.env["poliedro.dian.send.batch"].create({
            "company_id": self.company.id,
            "move_ids": [(6, 0, [accepted.id, queued.id, rejected.id])],
        })

        progress = self.env["poliedro.dian.send.batch"].get_navbar_progress()

        self.assertEqual(progress["total"], 3)
        self.assertEqual(progress["accepted"], 1)
        self.assertEqual(progress["queued"], 1)
        self.assertEqual(progress["failed"], 1)
        self.assertEqual(progress["percent"], 67)
        self.assertTrue(progress["is_active"])
        self.assertEqual(progress["errors"][0]["reason"], "Invalid test reason")
