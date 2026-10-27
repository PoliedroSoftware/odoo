# Poliedro DIAN Batch Progress

Adds a compact progress indicator to the Accounting invoices navbar. It follows
native Odoo invoice sends, displays accepted, queued, awaiting-response, and
failed/rejected totals, and shows DIAN's error message for failed documents.

The native `account.move.send` workflow remains responsible for generating and
transmitting documents. Its scheduled worker processes one queued accounting
document per run, and the cron interval is set to one minute. This deliberate
rate is one document per minute; a batch of 160 therefore takes up to about 160
minutes, plus the time needed for each DIAN request and PDF.

Install or upgrade in the target database with:

```powershell
.\.venv\Scripts\python.exe odoo-bin -c odoo.conf -d odoo_dev --stop-after-init --no-http --max-cron-threads=0 -i poliedro_dian_batch_progress
```

The counter tracks batches initiated after installation. It does not create or
resend invoices and it does not change already issued documents. A rejected
invoice remains visible with the response reason; retry remains an operator
action through Odoo's native invoice-send flow.
